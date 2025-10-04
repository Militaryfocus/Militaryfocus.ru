"""
API endpoints для загрузки файлов
"""
import os
from flask import Blueprint, request, jsonify, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from PIL import Image
import mimetypes
from datetime import datetime

from config.database import db
from middleware.rate_limit import limiter

bp = Blueprint('uploads', __name__)

# Разрешенные расширения
ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'document': {'pdf', 'doc', 'docx', 'txt', 'odt'},
    'video': {'mp4', 'avi', 'mov', 'mkv', 'webm'},
    'audio': {'mp3', 'wav', 'ogg', 'flac'}
}

def allowed_file(filename, file_type='image'):
    """Проверка разрешенного расширения файла"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())

def get_file_size(file):
    """Получить размер файла"""
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    return size

def optimize_image(file_path, max_width=1920, max_height=1080, quality=85):
    """Оптимизация изображения"""
    try:
        with Image.open(file_path) as img:
            # Конвертируем в RGB если нужно
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Изменяем размер если нужно
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Сохраняем с оптимизацией
            img.save(file_path, 'JPEG', optimize=True, quality=quality)
            
            return True
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return False

@bp.route('/image', methods=['POST'])
@jwt_required()
@limiter.limit("10 per hour")
def upload_image():
    """Загрузить изображение"""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if not allowed_file(file.filename, 'image'):
        return jsonify({'error': 'Недопустимый формат файла'}), 400
    
    # Проверка размера файла
    file_size = get_file_size(file)
    max_size = current_app.config.get('MAX_IMAGE_SIZE', 5 * 1024 * 1024)  # 5MB
    
    if file_size > max_size:
        return jsonify({'error': f'Файл слишком большой. Максимум {max_size // 1024 // 1024}MB'}), 400
    
    # Генерация уникального имени
    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    # Создание директории если нужно
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    year_month = datetime.utcnow().strftime('%Y/%m')
    upload_path = os.path.join(upload_folder, 'images', year_month)
    os.makedirs(upload_path, exist_ok=True)
    
    # Сохранение файла
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Оптимизация изображения
    optimize = request.form.get('optimize', 'true').lower() == 'true'
    if optimize:
        optimize_image(file_path)
    
    # Получение информации о файле
    with Image.open(file_path) as img:
        width, height = img.size
    
    # Формирование URL
    relative_path = os.path.join('images', year_month, filename)
    file_url = f"/uploads/{relative_path}"
    
    return jsonify({
        'success': True,
        'file': {
            'url': file_url,
            'filename': filename,
            'size': os.path.getsize(file_path),
            'width': width,
            'height': height,
            'mime_type': mimetypes.guess_type(file_path)[0]
        }
    }), 201

@bp.route('/avatar', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def upload_avatar():
    """Загрузить аватар пользователя"""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    if not allowed_file(file.filename, 'image'):
        return jsonify({'error': 'Недопустимый формат файла'}), 400
    
    # Проверка размера
    file_size = get_file_size(file)
    max_size = 2 * 1024 * 1024  # 2MB для аватаров
    
    if file_size > max_size:
        return jsonify({'error': 'Файл слишком большой. Максимум 2MB'}), 400
    
    # Генерация имени файла
    current_user_id = get_jwt_identity()
    filename = secure_filename(file.filename)
    ext = os.path.splitext(filename)[1]
    filename = f"avatar_{current_user_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}{ext}"
    
    # Создание директории
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    avatar_path = os.path.join(upload_folder, 'avatars')
    os.makedirs(avatar_path, exist_ok=True)
    
    # Сохранение файла
    file_path = os.path.join(avatar_path, filename)
    file.save(file_path)
    
    # Обработка аватара - квадратная обрезка и изменение размера
    try:
        with Image.open(file_path) as img:
            # Конвертируем в RGB
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Квадратная обрезка
            size = min(img.size)
            left = (img.width - size) // 2
            top = (img.height - size) // 2
            right = left + size
            bottom = top + size
            img = img.crop((left, top, right, bottom))
            
            # Изменение размера
            img = img.resize((200, 200), Image.Resampling.LANCZOS)
            
            # Сохранение
            img.save(file_path, 'JPEG', optimize=True, quality=90)
    except Exception as e:
        os.remove(file_path)
        return jsonify({'error': 'Ошибка обработки изображения'}), 500
    
    # Обновление пользователя
    from models import User
    user = User.query.get(current_user_id)
    if user:
        # Удаляем старый аватар если есть
        if user.avatar and user.avatar.startswith('/uploads/'):
            old_path = user.avatar.replace('/uploads/', '')
            old_file = os.path.join(upload_folder, old_path)
            if os.path.exists(old_file):
                try:
                    os.remove(old_file)
                except:
                    pass
        
        user.avatar = f"/uploads/avatars/{filename}"
        db.session.commit()
    
    return jsonify({
        'success': True,
        'avatar_url': f"/uploads/avatars/{filename}"
    }), 201

@bp.route('/file', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def upload_file():
    """Загрузить файл (документ)"""
    if 'file' not in request.files:
        return jsonify({'error': 'Файл не найден'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    
    # Определение типа файла
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    file_type = None
    
    for f_type, extensions in ALLOWED_EXTENSIONS.items():
        if ext in extensions:
            file_type = f_type
            break
    
    if not file_type:
        return jsonify({'error': 'Недопустимый формат файла'}), 400
    
    # Проверка размера
    file_size = get_file_size(file)
    max_size = current_app.config.get('MAX_FILE_SIZE', 10 * 1024 * 1024)  # 10MB
    
    if file_size > max_size:
        return jsonify({'error': f'Файл слишком большой. Максимум {max_size // 1024 // 1024}MB'}), 400
    
    # Генерация имени файла
    filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    name, ext = os.path.splitext(filename)
    filename = f"{name}_{timestamp}{ext}"
    
    # Создание директории
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    year_month = datetime.utcnow().strftime('%Y/%m')
    upload_path = os.path.join(upload_folder, file_type + 's', year_month)
    os.makedirs(upload_path, exist_ok=True)
    
    # Сохранение файла
    file_path = os.path.join(upload_path, filename)
    file.save(file_path)
    
    # Формирование URL
    relative_path = os.path.join(file_type + 's', year_month, filename)
    file_url = f"/uploads/{relative_path}"
    
    return jsonify({
        'success': True,
        'file': {
            'url': file_url,
            'filename': filename,
            'size': os.path.getsize(file_path),
            'type': file_type,
            'mime_type': mimetypes.guess_type(file_path)[0]
        }
    }), 201

@bp.route('/<path:filepath>', methods=['GET'])
def serve_file(filepath):
    """Отдача загруженных файлов"""
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    file_path = os.path.join(upload_folder, filepath)
    
    if not os.path.exists(file_path) or not os.path.isfile(file_path):
        return jsonify({'error': 'Файл не найден'}), 404
    
    # Безопасность - проверка что файл внутри upload_folder
    real_path = os.path.realpath(file_path)
    upload_real_path = os.path.realpath(upload_folder)
    
    if not real_path.startswith(upload_real_path):
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    return send_file(file_path)