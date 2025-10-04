"""
Утилиты для работы с капчей
"""
import os
import random
import string
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import base64

class SimpleCaptcha:
    """Простая капча без внешних сервисов"""
    
    def __init__(self, width=200, height=60):
        self.width = width
        self.height = height
        self.chars = string.ascii_uppercase + string.digits
        self.font_size = 40
        
    def generate(self, length=6):
        """Генерирует капчу и возвращает текст и изображение в base64"""
        # Генерируем случайный текст
        text = ''.join(random.choices(self.chars, k=length))
        
        # Создаем изображение
        image = Image.new('RGB', (self.width, self.height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Пытаемся использовать системный шрифт
        try:
            font = ImageFont.truetype('/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf', self.font_size)
        except:
            # Используем стандартный шрифт если системный не найден
            font = ImageFont.load_default()
        
        # Добавляем шум - случайные точки
        for _ in range(random.randint(100, 200)):
            x = random.randint(0, self.width)
            y = random.randint(0, self.height)
            draw.point((x, y), fill=random.choice(['gray', 'lightgray', 'darkgray']))
        
        # Добавляем линии для усложнения
        for _ in range(random.randint(3, 5)):
            x1 = random.randint(0, self.width)
            y1 = random.randint(0, self.height)
            x2 = random.randint(0, self.width)
            y2 = random.randint(0, self.height)
            draw.line([(x1, y1), (x2, y2)], fill='lightgray', width=1)
        
        # Рисуем текст
        char_width = self.width // length
        for i, char in enumerate(text):
            # Случайный цвет для каждого символа
            color = random.choice(['black', 'darkblue', 'darkgreen', 'darkred'])
            
            # Случайное смещение и поворот
            x = i * char_width + random.randint(5, 15)
            y = random.randint(5, 20)
            
            # Рисуем символ
            draw.text((x, y), char, font=font, fill=color)
        
        # Применяем легкое размытие
        image = image.filter(ImageFilter.SMOOTH_MORE)
        
        # Конвертируем в base64
        buffered = BytesIO()
        image.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return text, f"data:image/png;base64,{img_str}"
    
    @staticmethod
    def verify(stored_text, user_input):
        """Проверяет введенную капчу"""
        if not stored_text or not user_input:
            return False
        
        # Сравниваем без учета регистра
        return stored_text.upper() == user_input.upper()


class ReCaptchaField:
    """Поле для Google reCAPTCHA"""
    
    @staticmethod
    def get_html(sitekey):
        """Возвращает HTML код для reCAPTCHA"""
        return f'''
        <div class="g-recaptcha mb-3" data-sitekey="{sitekey}"></div>
        <script src="https://www.google.com/recaptcha/api.js" async defer></script>
        '''
    
    @staticmethod
    def verify(response, secret_key, remote_ip=None):
        """Проверяет ответ reCAPTCHA"""
        import requests
        
        data = {
            'secret': secret_key,
            'response': response
        }
        
        if remote_ip:
            data['remoteip'] = remote_ip
        
        try:
            r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
            result = r.json()
            return result.get('success', False)
        except:
            return False