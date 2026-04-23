import os
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Material, Submission
from forms import RegistrationForm, LoginForm, SMSVerificationForm, AddSubmissionForm
from utils import generate_sms_code, send_sms, sync_materials_table
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()
    sync_materials_table(db, Material)

    # Первый администратор (если нет ни одного)
    admin = db.session.query(User).filter_by(is_admin=True).first()
    if not admin:
        admin_user = User(
            phone='79001234567',
            full_name='Администратор Системы',
            password_hash=generate_password_hash('admin123'),
            is_verified=True,
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        logger.info("Default admin created: 79001234567 / admin123")


def admin_required(f):
    from functools import wraps
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)

    return decorated_function


def normalize_phone(phone: str) -> str:
    digits = ''.join(filter(str.isdigit, phone))
    if not digits:
        return ''
    if digits.startswith('8'):
        digits = '7' + digits[1:]
    elif not digits.startswith('7'):
        if len(digits) == 10:
            digits = '7' + digits
    return digits


@app.route('/')
def index():
    # Рейтинг (топ-10 обычных подтверждённых пользователей)
    users = db.session.query(User).filter_by(is_verified=True, is_admin=False).all()
    rating = []
    for u in users:
        rating.append({
            'id': u.id,
            'full_name': u.full_name,
            'points': u.get_total_points()
        })
    rating.sort(key=lambda x: x['points'], reverse=True)
    top_rating = rating[:10]

    # Данные для графика
    personal_dates = []
    personal_weights = []
    if current_user.is_authenticated:
        subs = (db.session.query(
            db.func.date(Submission.created_at).label('date'),
            db.func.sum(Submission.weight_kg).label('total_weight'))
                .filter(Submission.user_id == current_user.id)
                .group_by(db.func.date(Submission.created_at))
                .order_by('date')
                .all())
        for row in subs:
            # row.date уже строка от func.date()
            personal_dates.append(str(row.date))
            personal_weights.append(round(row.total_weight, 2))

    # Среднее по всем обычным пользователям
    all_subs = (db.session.query(
        db.func.date(Submission.created_at).label('date'),
        db.func.sum(Submission.weight_kg).label('total_weight'),
        db.func.count(db.distinct(Submission.user_id)).label('user_count'))
                .join(User, Submission.user_id == User.id)
                .filter(User.is_admin == False)
                .group_by(db.func.date(Submission.created_at))
                .order_by('date')
                .all())

    avg_dates = []
    avg_weights = []
    for row in all_subs:
        avg_weight = round(row.total_weight / row.user_count, 2) if row.user_count else 0
        avg_dates.append(str(row.date))
        avg_weights.append(avg_weight)

    return render_template('index.html',
                           rating=top_rating,
                           personal_dates=personal_dates,
                           personal_weights=personal_weights,
                           avg_dates=avg_dates,
                           avg_weights=avg_weights)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        phone_clean = normalize_phone(form.phone.data)
        existing_user = db.session.query(User).filter_by(phone=phone_clean).first()
        if existing_user:
            flash('Этот номер телефона уже зарегистрирован.', 'danger')
            return render_template('register.html', form=form)

        user = User(
            phone=phone_clean,
            full_name=form.full_name.data,
            password_hash=generate_password_hash(form.password.data),
            is_verified=False,
            is_admin=False
        )
        code = generate_sms_code()
        user.sms_code = code
        user.sms_code_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.add(user)
        db.session.commit()

        logger.info(f"New user registered: {user.phone}, code: {code}")
        message = f"Код подтверждения EcoBird: {code}"

        if send_sms(user.phone, message):
            flash('На ваш номер отправлен код подтверждения.', 'info')
        else:
            flash('Не удалось отправить SMS. Попробуйте позже или обратитесь к администратору.', 'danger')
            logger.error(f"Failed to send SMS to {user.phone}")

        return redirect(url_for('verify', user_id=user.id))
    return render_template('register.html', form=form)


@app.route('/verify/<int:user_id>', methods=['GET', 'POST'])
def verify(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.is_verified:
        flash('Аккаунт уже подтверждён.', 'info')
        return redirect(url_for('login'))
    form = SMSVerificationForm()
    if form.validate_on_submit():
        if user.sms_code == form.code.data and user.sms_code_expires and user.sms_code_expires > datetime.utcnow():
            user.is_verified = True
            user.sms_code = None
            user.sms_code_expires = None
            db.session.commit()
            logger.info(f"User verified: {user.phone}")
            flash('Телефон подтверждён! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Неверный или просроченный код.', 'danger')
    return render_template('verify.html', form=form, user=user)


@app.route('/resend_code/<int:user_id>')
def resend_code(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    if user.is_verified:
        flash('Аккаунт уже подтверждён.', 'info')
        return redirect(url_for('login'))

    code = generate_sms_code()
    user.sms_code = code
    user.sms_code_expires = datetime.utcnow() + timedelta(minutes=10)
    db.session.commit()

    logger.info(f"Resending code to {user.phone}: {code}")
    message = f"Код подтверждения EcoBird: {code}"

    if send_sms(user.phone, message):
        flash('Новый код отправлен на ваш номер.', 'success')
    else:
        flash('Ошибка отправки SMS. Попробуйте позже.', 'danger')

    return redirect(url_for('verify', user_id=user.id))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        phone_clean = normalize_phone(form.phone.data)
        user = db.session.query(User).filter_by(phone=phone_clean).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            if not user.is_verified:
                flash('Аккаунт не подтверждён. Пожалуйста, подтвердите номер телефона.', 'warning')
                return redirect(url_for('verify', user_id=user.id))
            login_user(user, remember=True)
            logger.info(f"User logged in: {user.phone}")
            flash(f'Добро пожаловать, {user.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Неверный номер телефона или пароль.', 'danger')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('index'))


@app.route('/profile')
@login_required
def profile():
    submissions = current_user.submissions.order_by(Submission.created_at.desc()).all()
    total_points = current_user.get_total_points()
    return render_template('profile.html', user=current_user, submissions=submissions, total_points=total_points)


@app.route('/admin')
@admin_required
def admin_dashboard():
    users = db.session.query(User).all()
    return render_template('admin/dashboard.html', users=users)


@app.route('/admin/submissions/add', methods=['GET', 'POST'])
@admin_required
def add_submission():
    form = AddSubmissionForm()
    users = db.session.query(User).filter_by(is_verified=True).all()
    form.user_id.choices = [(u.id, f"{u.full_name} ({u.phone})") for u in users]
    materials = db.session.query(Material).all()
    form.material_key.choices = [(m.key, f"{m.name} (коэф. {m.coefficient})") for m in materials]

    preselected_user_id = request.args.get('user_id', type=int)
    if preselected_user_id and request.method == 'GET':
        form.user_id.data = preselected_user_id

    if form.validate_on_submit():
        user = db.session.get(User, form.user_id.data)
        material = db.session.get(Material, form.material_key.data)
        weight = form.weight_kg.data
        points = weight * material.coefficient
        submission = Submission(
            user_id=user.id,
            material_key=material.key,
            weight_kg=weight,
            points=points,
            admin_id=current_user.id
        )
        db.session.add(submission)
        db.session.commit()
        logger.info(
            f"Admin {current_user.full_name} added submission for {user.full_name}: {weight}kg of {material.name}, points: {points}")
        flash(f'✅ Запись о сдаче для {user.full_name} добавлена. Баллы: {points:.2f}', 'success')
        return redirect(url_for('admin_users'))

    return render_template('admin/add_submission.html', form=form)


@app.route('/admin/users')
@admin_required
def admin_users():
    users = db.session.query(User).order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@app.route('/api/user/<int:user_id>/submissions')
@admin_required
def api_user_submissions(user_id):
    user = db.session.get(User, user_id)
    if not user:
        abort(404)
    submissions = user.submissions.order_by(Submission.created_at.desc()).all()
    result = {
        'user_name': user.full_name,
        'user_phone': user.phone,
        'total_points': user.get_total_points(),
        'submissions': []
    }
    for sub in submissions:
        admin_name = None
        if sub.admin_id:
            admin = db.session.get(User, sub.admin_id)
            admin_name = admin.full_name if admin else None
        result['submissions'].append({
            'id': sub.id,
            'created_at': sub.created_at.isoformat(),
            'material_name': sub.material.name,
            'material_key': sub.material_key,
            'weight_kg': sub.weight_kg,
            'coefficient': sub.material.coefficient,
            'points': sub.points,
            'admin_name': admin_name
        })
    return jsonify(result)


@app.route('/api/rating')
def api_rating():
    users = db.session.query(User).filter_by(is_verified=True, is_admin=False).all()
    rating = []
    for u in users:
        rating.append({
            'full_name': u.full_name,
            'points': u.get_total_points()
        })
    rating.sort(key=lambda x: x['points'], reverse=True)
    return jsonify(rating)


# Обработчики ошибок
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', error_code=403, error_message='Доступ запрещён'), 403


@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_message='Страница не найдена'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error_code=500, error_message='Внутренняя ошибка сервера'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)