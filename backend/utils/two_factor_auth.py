"""
Двухфакторная аутентификация для администраторов
"""
import pyotp
import qrcode
from io import BytesIO
import base64
from datetime import datetime, timedelta

class TwoFactorAuth:
    """Менеджер двухфакторной аутентификации"""
    
    def __init__(self, app_name="Military Focus Blog"):
        self.app_name = app_name
        self.interval = 30  # Интервал обновления кода в секундах
        
    def generate_secret(self):
        """Генерирует секретный ключ для пользователя"""
        return pyotp.random_base32()
    
    def get_totp_uri(self, username, secret):
        """Получает URI для генерации QR кода"""
        return pyotp.totp.TOTP(secret).provisioning_uri(
            name=username,
            issuer_name=self.app_name
        )
    
    def generate_qr_code(self, username, secret):
        """Генерирует QR код для настройки 2FA"""
        # Получаем URI
        uri = self.get_totp_uri(username, secret)
        
        # Создаем QR код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Конвертируем в base64
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    def verify_token(self, secret, token, window=1):
        """
        Проверяет токен
        
        Args:
            secret: Секретный ключ пользователя
            token: Введенный токен
            window: Окно валидности (количество интервалов)
            
        Returns:
            bool: True если токен валиден
        """
        if not secret or not token:
            return False
        
        try:
            totp = pyotp.TOTP(secret)
            # Проверяем с учетом временного окна для компенсации рассинхронизации
            return totp.verify(token, valid_window=window)
        except:
            return False
    
    def get_current_token(self, secret):
        """Получает текущий токен (для тестирования)"""
        if not secret:
            return None
        
        try:
            totp = pyotp.TOTP(secret)
            return totp.now()
        except:
            return None
    
    def get_backup_codes(self, count=10, length=8):
        """Генерирует резервные коды"""
        import secrets
        import string
        
        codes = []
        chars = string.ascii_uppercase + string.digits
        
        for _ in range(count):
            code = ''.join(secrets.choice(chars) for _ in range(length))
            # Форматируем код для удобства: XXXX-XXXX
            formatted = f"{code[:4]}-{code[4:]}"
            codes.append(formatted)
        
        return codes
    
    def verify_backup_code(self, code, stored_codes):
        """Проверяет резервный код"""
        if not code or not stored_codes:
            return False
        
        # Нормализуем код
        normalized_code = code.upper().replace('-', '').replace(' ', '')
        
        for stored_code in stored_codes:
            normalized_stored = stored_code.upper().replace('-', '').replace(' ', '')
            if normalized_code == normalized_stored:
                return True
        
        return False


class TwoFactorSession:
    """Управление сессиями 2FA"""
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.prefix = "2fa:session:"
        self.ttl = 300  # 5 минут
    
    def create_verification_session(self, user_id):
        """Создает временную сессию для верификации 2FA"""
        if not self.redis_client:
            return None
        
        import secrets
        session_id = secrets.token_urlsafe(32)
        key = f"{self.prefix}{session_id}"
        
        data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'verified': False
        }
        
        try:
            self.redis_client.hmset(key, data)
            self.redis_client.expire(key, self.ttl)
            return session_id
        except:
            return None
    
    def verify_session(self, session_id):
        """Помечает сессию как верифицированную"""
        if not self.redis_client:
            return False
        
        key = f"{self.prefix}{session_id}"
        
        try:
            self.redis_client.hset(key, 'verified', 'true')
            self.redis_client.hset(key, 'verified_at', datetime.utcnow().isoformat())
            return True
        except:
            return False
    
    def check_session(self, session_id):
        """Проверяет статус сессии"""
        if not self.redis_client:
            return None
        
        key = f"{self.prefix}{session_id}"
        
        try:
            data = self.redis_client.hgetall(key)
            if not data:
                return None
            
            # Преобразуем bytes в строки
            result = {}
            for k, v in data.items():
                k_str = k.decode() if isinstance(k, bytes) else k
                v_str = v.decode() if isinstance(v, bytes) else v
                result[k_str] = v_str
            
            result['verified'] = result.get('verified', 'false') == 'true'
            
            return result
        except:
            return None
    
    def delete_session(self, session_id):
        """Удаляет сессию"""
        if not self.redis_client:
            return False
        
        key = f"{self.prefix}{session_id}"
        
        try:
            self.redis_client.delete(key)
            return True
        except:
            return False