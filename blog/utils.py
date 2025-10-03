"""
Утилиты для валидации файлов и безопасности
"""

import os
import magic
from flask import current_app, request
from werkzeug.utils import secure_filename
import logging

security_logger = logging.getLogger('security')

def allowed_file(filename):
    """Проверка разрешенных расширений файлов"""
    if not filename:
        return False
    
    # Получаем расширение файла
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in current_app.config['ALLOWED_EXTENSIONS']

def validate_file_size(file):
    """Проверка размера файла"""
    if not file:
        return False, "Файл не предоставлен"
    
    # Проверяем размер файла
    file.seek(0, 2)  # Переходим в конец файла
    file_size = file.tell()
    file.seek(0)  # Возвращаемся в начало
    
    max_size = current_app.config['MAX_FILE_SIZE']
    
    if file_size > max_size:
        security_logger.warning(f"File too large: {file_size} bytes from {request.remote_addr}")
        return False, f"Файл слишком большой. Максимальный размер: {max_size // (1024*1024)}MB"
    
    return True, "OK"

def validate_file_content(file):
    """Проверка содержимого файла с помощью magic numbers"""
    if not file:
        return False, "Файл не предоставлен"
    
    try:
        # Читаем первые несколько байт для определения типа файла
        file.seek(0)
        file_header = file.read(1024)
        file.seek(0)
        
        # Определяем MIME тип
        mime_type = magic.from_buffer(file_header, mime=True)
        
        # Разрешенные MIME типы
        allowed_mime_types = {
            'image/png', 'image/jpeg', 'image/gif',
            'application/pdf', 'text/plain',
            'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        }
        
        if mime_type not in allowed_mime_types:
            security_logger.warning(f"Invalid file type: {mime_type} from {request.remote_addr}")
            return False, f"Неподдерживаемый тип файла: {mime_type}"
        
        return True, "OK"
        
    except Exception as e:
        security_logger.error(f"File validation error: {e}")
        return False, "Ошибка проверки файла"

def secure_filename_custom(filename):
    """Безопасное имя файла с дополнительными проверками"""
    if not filename:
        return None
    
    # Используем Werkzeug для безопасного имени
    secure_name = secure_filename(filename)
    
    # Дополнительные проверки
    if not secure_name or secure_name in ['.', '..']:
        return None
    
    # Проверяем на подозрительные символы
    suspicious_chars = ['..', '/', '\\', ':', '*', '?', '"', '<', '>', '|']
    for char in suspicious_chars:
        if char in secure_name:
            security_logger.warning(f"Suspicious filename: {filename} from {request.remote_addr}")
            return None
    
    return secure_name

def validate_upload_file(file, filename):
    """Комплексная валидация загружаемого файла"""
    
    # Проверка расширения
    if not allowed_file(filename):
        return False, "Неподдерживаемое расширение файла"
    
    # Проверка размера
    size_valid, size_msg = validate_file_size(file)
    if not size_valid:
        return False, size_msg
    
    # Проверка содержимого
    content_valid, content_msg = validate_file_content(file)
    if not content_valid:
        return False, content_msg
    
    # Безопасное имя файла
    secure_name = secure_filename_custom(filename)
    if not secure_name:
        return False, "Недопустимое имя файла"
    
    return True, secure_name

def get_file_info(file):
    """Получение информации о файле"""
    if not file:
        return None
    
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    
    return {
        'size': size,
        'size_mb': round(size / (1024 * 1024), 2),
        'name': file.filename if hasattr(file, 'filename') else 'unknown'
    }