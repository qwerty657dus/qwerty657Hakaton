import random
import string
import requests
import urllib.parse
from flask import current_app
from coefficients import ECO_COEFFICIENTS

def generate_sms_code(length=6):
    """Генерация случайного цифрового кода."""
    return ''.join(random.choices(string.digits, k=length))

def send_sms(phone, message):
    """
    Отправка SMS через TargetSMS API (GET-запрос).
    Возвращает True при успешной отправке, иначе False.
    """
    # Тестовый режим — вывод кода в консоль
    if current_app.config.get('SMS_TEST_MODE'):
        print(f"\n{'='*50}")
        print(f"[SMS TEST] Номер: {phone}")
        print(f"[SMS TEST] Текст: {message}")
        print(f"{'='*50}\n")
        return True

    api_url = current_app.config.get('TARGETSMS_API_URL')
    user = current_app.config.get('TARGETSMS_USER', '')
    pwd = current_app.config.get('TARGETSMS_PWD', '')
    sender = current_app.config.get('TARGETSMS_SENDER', 'targettele')

    if not api_url:
        current_app.logger.error("TargetSMS API URL not configured.")
        return False

    # Параметры запроса (все строки, кроме телефона, будут автоматически URL-закодированы)
    params = {
        'user': user,
        'pwd': pwd,
        'name_delivery': 'verificationcode',  # название рассылки для статистики
        'sadr': sender,
        'dadr': str(phone),                   # номер в формате 79001234567
        'text': message
    }

    # Логируем URL для отладки (без пароля)
    debug_params = params.copy()
    if pwd:
        debug_params['pwd'] = '***'
    debug_url = f"{api_url}?{urllib.parse.urlencode(debug_params)}"
    current_app.logger.info(f"Sending SMS: {debug_url}")

    try:
        # GET-запрос с параметрами
        response = requests.get(api_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        response_text = response.text.strip()

        current_app.logger.info(f"SMS API response: '{response_text}'")

        # Проверяем, не вернулся ли текст ошибки
        error_keywords = [
            'error', 'закончились', 'заблокирован', 'Укажите номер',
            'стоп-листе', 'закрыто', 'Недостаточно средств',
            'отклонен', 'Нет отправителя', 'не должен превышать',
            'Нет текста', 'Такого отправителя', 'не прошел модерацию'
        ]

        for keyword in error_keywords:
            if keyword.lower() in response_text.lower():
                current_app.logger.error(f"SMS API error: {response_text}")
                return False

        # Успешный ответ — число или числа через запятую
        if response_text and response_text.replace(',', '').isdigit():
            current_app.logger.info(f"SMS sent successfully, ID: {response_text}")
            return True
        else:
            current_app.logger.error(f"Unexpected SMS API response: '{response_text}'")
            return False

    except requests.RequestException as e:
        current_app.logger.error(f"SMS request failed: {e}")
        return False

def sync_materials_table(db, Material):
    """Синхронизация справочника материалов с коэффициентами."""
    for key, data in ECO_COEFFICIENTS.items():
        mat = Material.query.get(key)
        if not mat:
            mat = Material(key=key)
        mat.name = data['name']
        mat.group = data['group']
        mat.coefficient = data['coefficient']
        mat.unit = data.get('unit', 'kg')
        mat.note = data.get('note', '')
        db.session.add(mat)
    db.session.commit()