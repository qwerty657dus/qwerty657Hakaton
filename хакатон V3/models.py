from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_verified = db.Column(db.Boolean, default=False)
    sms_code = db.Column(db.String(6), nullable=True)
    sms_code_expires = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    submissions = db.relationship('Submission', backref='user', lazy='dynamic',
                                  foreign_keys='Submission.user_id')
    added_submissions = db.relationship('Submission', backref='admin', lazy='dynamic',
                                        foreign_keys='Submission.admin_id')

    def get_total_points(self):
        """Возвращает сумму баллов, если пользователь подтверждён, иначе 0."""
        if not self.is_verified:
            return 0.0
        return db.session.query(db.func.sum(Submission.points)).filter_by(user_id=self.id).scalar() or 0.0

class Material(db.Model):
    __tablename__ = 'materials'
    key = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    group = db.Column(db.String(50), nullable=False)
    coefficient = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(10), default='kg')
    note = db.Column(db.Text, nullable=True)

    submissions = db.relationship('Submission', backref='material', lazy='dynamic')

class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    material_key = db.Column(db.String(50), db.ForeignKey('materials.key'), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    points = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)