import random
import time
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
from app import app, db, User, Material, Submission
from utils import sync_materials_table

# ------------------------------
# Настройки
# ------------------------------
TOTAL_USERS = 100
UNVERIFIED_COUNT = 10
DAYS_BACK = 30
PASSWORD = 'test123'
SUBMISSION_PROBABILITY = 0.6
MAX_SUBMISSIONS_PER_DAY = 3
WEIGHT_MIN = 0.1
WEIGHT_MAX = 5.0

FIRST_NAMES_MALE = ['Александр','Михаил','Иван','Дмитрий','Андрей','Сергей','Алексей','Николай','Владимир','Павел']
FIRST_NAMES_FEMALE = ['Мария','Елена','Ольга','Анна','Татьяна','Екатерина','Наталья','Ирина','Светлана','Юлия']
LAST_NAMES = ['Иванов','Петров','Сидоров','Смирнов','Кузнецов','Васильев','Попов','Новиков','Фёдоров','Морозов',
              'Волков','Алексеев','Лебедев','Семёнов','Егоров','Павлов','Козлов','Степанов','Николаев','Орлов']
MIDDLE_NAMES_MALE = ['Александрович','Михайлович','Иванович','Дмитриевич','Андреевич','Сергеевич','Алексеевич','Николаевич','Владимирович','Павлович']
MIDDLE_NAMES_FEMALE = ['Александровна','Михайловна','Ивановна','Дмитриевна','Андреевна','Сергеевна','Алексеевна','Николаевна','Владимировна','Павловна']

def random_phone():
    return '79' + ''.join(random.choices('0123456789', k=9))

def random_full_name():
    if random.choice([True, False]):
        return f"{random.choice(LAST_NAMES)} {random.choice(FIRST_NAMES_MALE)} {random.choice(MIDDLE_NAMES_MALE)}"
    else:
        return f"{random.choice(LAST_NAMES)}а {random.choice(FIRST_NAMES_FEMALE)} {random.choice(MIDDLE_NAMES_FEMALE)}"

def safe_commit():
    """Повторяет коммит при блокировке базы (SQLite busy)"""
    for i in range(15):
        try:
            db.session.commit()
            return
        except Exception as e:
            db.session.rollback()
            if 'database is locked' in str(e).lower():
                wait = 1 + i * 0.3
                print(f"База занята, попытка {i+1}/15, ждём {wait:.1f} сек...")
                time.sleep(wait)
            else:
                raise
    raise Exception("Не удалось выполнить коммит после многих попыток.")

def main():
    print("\n" + "="*60)
    print("Убедитесь, что Flask-сервер остановлен!")
    print("="*60 + "\n")
    input("Нажмите Enter для продолжения...")

    with app.app_context():
        # Инициализация таблиц (если их нет) и синхронизация материалов
        db.create_all()
        sync_materials_table(db, Material)

        materials = Material.query.all()
        if not materials:
            print("Ошибка: нет материалов в таблице.")
            return
        material_keys = [m.key for m in materials]

        # Очистка базы
        print("Очистка базы...")
        try:
            Submission.query.delete()
            User.query.delete()
            safe_commit()
        except Exception as e:
            db.session.rollback()
            print(f"Не удалось очистить базу: {e}")
            print("Попробуйте перезагрузить компьютер и повторить.")
            return
        print("База очищена.")

        # Администратор
        admin = User(
            phone='79001234567',
            full_name='Администратор Системы',
            password_hash=generate_password_hash('admin123'),
            is_verified=True,
            is_admin=True,
            created_at=datetime.utcnow()
        )
        db.session.add(admin)
        safe_commit()
        print("Администратор создан: 79001234567 / admin123")

        # Обычные пользователи
        users = []
        for i in range(TOTAL_USERS):
            is_verified = i >= UNVERIFIED_COUNT
            user = User(
                phone=random_phone(),
                full_name=random_full_name(),
                password_hash=generate_password_hash(PASSWORD),
                is_verified=is_verified,
                is_admin=False,
                created_at=datetime.utcnow() - timedelta(days=DAYS_BACK)
            )
            # Уникальный телефон
            while User.query.filter_by(phone=user.phone).first():
                user.phone = random_phone()
            users.append(user)

        db.session.add_all(users)
        safe_commit()
        print(f"Создано {TOTAL_USERS} обычных пользователей (пароль: {PASSWORD}).")

        # Генерация сдач
        today = datetime.utcnow().date()
        batch = []
        for idx, user in enumerate(users, 1):
            if idx % 10 == 0:
                print(f"Обрабатываю пользователя {idx}/{len(users)}...")
            for day_offset in range(DAYS_BACK):
                day = today - timedelta(days=day_offset)
                if random.random() < SUBMISSION_PROBABILITY:
                    num_subs = random.randint(1, MAX_SUBMISSIONS_PER_DAY)
                    for _ in range(num_subs):
                        mat_key = random.choice(material_keys)
                        material = Material.query.get(mat_key)
                        weight = round(random.uniform(WEIGHT_MIN, WEIGHT_MAX), 2)
                        points = round(weight * material.coefficient, 2)
                        ts = datetime.combine(day, datetime.min.time()) + timedelta(hours=random.randint(8, 20))
                        sub = Submission(
                            user_id=user.id,
                            material_key=mat_key,
                            weight_kg=weight,
                            points=points,
                            created_at=ts,
                            admin_id=admin.id
                        )
                        batch.append(sub)
                        if len(batch) >= 500:
                            db.session.add_all(batch)
                            safe_commit()
                            batch = []
        if batch:
            db.session.add_all(batch)
            safe_commit()

        print(f"Всего записей о сдаче: {Submission.query.count()}")
        print("Готово! Запускайте приложение.")

if __name__ == '__main__':
    main()