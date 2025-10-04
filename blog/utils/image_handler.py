"""
Обработчик изображений для блога
"""
import os
import hashlib
from datetime import datetime
from PIL import Image
from werkzeug.utils import secure_filename

class ImageHandler:
    """Класс для работы с изображениями"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Размеры для аватаров
    AVATAR_SIZES = {
        'small': (64, 64),
        'medium': (128, 128),
        'large': (256, 256)
    }
    
    # Размеры для постов
    POST_SIZES = {
        'thumb': (300, 200),
        'medium': (600, 400),
        'large': (1200, 630),  # Для социальных сетей
        'original': None
    }
    
    def __init__(self, upload_folder='blog/static/uploads'):
        self.upload_folder = upload_folder
        
    def allowed_file(self, filename):
        """Проверка разрешенного расширения файла"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def generate_filename(self, original_filename, prefix='img'):
        """Генерация уникального имени файла"""
        ext = original_filename.rsplit('.', 1)[1].lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        random_hash = hashlib.md5(original_filename.encode()).hexdigest()[:8]
        return f"{prefix}_{timestamp}_{random_hash}.{ext}"
    
    def save_avatar(self, file, user_id):
        """Сохранение и обработка аватара пользователя"""
        if not self.allowed_file(file.filename):
            raise ValueError("Недопустимый формат файла")
        
        # Генерируем имя файла
        filename = self.generate_filename(file.filename, f'user_{user_id}')
        filepath = os.path.join(self.upload_folder, 'avatars', filename)
        
        # Сохраняем оригинал
        file.save(filepath)
        
        # Обрабатываем изображение
        img = Image.open(filepath)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Обрезаем до квадрата
        img = self._crop_center_square(img)
        
        # Создаем разные размеры
        for size_name, size in self.AVATAR_SIZES.items():
            resized = img.resize(size, Image.Resampling.LANCZOS)
            size_filename = f"{size_name}_{filename}"
            size_filepath = os.path.join(self.upload_folder, 'avatars', size_filename)
            resized.save(size_filepath, 'JPEG', quality=85, optimize=True)
        
        # Сохраняем оригинал в квадрате
        img.save(filepath, 'JPEG', quality=90, optimize=True)
        
        return filename
    
    def save_post_image(self, file, post_id, image_type='featured'):
        """Сохранение изображения для поста"""
        if not self.allowed_file(file.filename):
            raise ValueError("Недопустимый формат файла")
        
        # Генерируем имя файла
        filename = self.generate_filename(file.filename, f'post_{post_id}_{image_type}')
        filepath = os.path.join(self.upload_folder, 'posts', filename)
        
        # Сохраняем оригинал
        file.save(filepath)
        
        # Обрабатываем изображение
        img = Image.open(filepath)
        
        # Конвертируем в RGB если нужно
        if img.mode in ('RGBA', 'LA'):
            rgb_img = Image.new('RGB', img.size, (255, 255, 255))
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = rgb_img
        
        # Создаем разные размеры
        for size_name, size in self.POST_SIZES.items():
            if size:  # Пропускаем 'original'
                resized = self._resize_image(img, size)
                size_filename = f"{size_name}_{filename}"
                size_filepath = os.path.join(self.upload_folder, 'posts', size_filename)
                resized.save(size_filepath, 'JPEG', quality=85, optimize=True)
        
        # Оптимизируем оригинал
        img.save(filepath, 'JPEG', quality=90, optimize=True)
        
        return filename
    
    def delete_image(self, filename, subfolder='posts'):
        """Удаление изображения и всех его размеров"""
        base_path = os.path.join(self.upload_folder, subfolder)
        
        # Удаляем оригинал
        filepath = os.path.join(base_path, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Удаляем все размеры
        for prefix in ['small_', 'medium_', 'large_', 'thumb_']:
            size_filepath = os.path.join(base_path, f"{prefix}{filename}")
            if os.path.exists(size_filepath):
                os.remove(size_filepath)
    
    def _crop_center_square(self, img):
        """Обрезка изображения до квадрата по центру"""
        width, height = img.size
        new_size = min(width, height)
        
        left = (width - new_size) // 2
        top = (height - new_size) // 2
        right = left + new_size
        bottom = top + new_size
        
        return img.crop((left, top, right, bottom))
    
    def _resize_image(self, img, max_size):
        """Изменение размера с сохранением пропорций"""
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    
    def get_image_url(self, filename, size=None, subfolder='posts'):
        """Получение URL изображения"""
        if size and size != 'original':
            filename = f"{size}_{filename}"
        
        return f"/static/uploads/{subfolder}/{filename}"
    
    def cleanup_temp(self):
        """Очистка временных файлов старше 24 часов"""
        import time
        
        temp_dir = os.path.join(self.upload_folder, 'temp')
        now = time.time()
        
        for filename in os.listdir(temp_dir):
            filepath = os.path.join(temp_dir, filename)
            if os.path.isfile(filepath):
                # Проверяем возраст файла
                if os.stat(filepath).st_mtime < now - 86400:  # 24 часа
                    os.remove(filepath)