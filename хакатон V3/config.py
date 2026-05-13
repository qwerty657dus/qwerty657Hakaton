import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///ecobird.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # TargetSMS API (GET-запросы)
    TARGETSMS_API_URL = os.environ.get('TARGETSMS_API_URL', 'https://sms.targetsms.ru/sendsms.php')
    TARGETSMS_USER = os.environ.get('TARGETSMS_USER')          # Логин
    TARGETSMS_PWD = os.environ.get('TARGETSMS_PWD')            # Пароль
    TARGETSMS_SENDER = os.environ.get('TARGETSMS_SENDER', 'EcoBird')  # Имя отправителя (до 11 латинских букв/цифр)

    SMS_TEST_MODE = os.environ.get('SMS_TEST_MODE', 'False').lower() in ('true', '1', 't')