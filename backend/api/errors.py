"""
Обработчики ошибок для API
"""
from flask import jsonify
from marshmallow import ValidationError
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import exceptions as jwt_exceptions

def register_error_handlers(app):
    """Регистрация обработчиков ошибок"""
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        """Обработка ошибок валидации Marshmallow"""
        return jsonify({
            'error': 'Ошибка валидации',
            'errors': e.messages
        }), 400
    
    @app.errorhandler(404)
    def handle_not_found(e):
        """Обработка 404"""
        return jsonify({
            'error': 'Ресурс не найден'
        }), 404
    
    @app.errorhandler(401)
    def handle_unauthorized(e):
        """Обработка 401"""
        return jsonify({
            'error': 'Требуется авторизация'
        }), 401
    
    @app.errorhandler(403)
    def handle_forbidden(e):
        """Обработка 403"""
        return jsonify({
            'error': 'Доступ запрещен'
        }), 403
    
    @app.errorhandler(500)
    def handle_internal_error(e):
        """Обработка 500"""
        return jsonify({
            'error': 'Внутренняя ошибка сервера'
        }), 500
    
    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        """Обработка ошибок целостности БД"""
        return jsonify({
            'error': 'Ошибка целостности данных',
            'message': 'Возможно, такая запись уже существует'
        }), 400
    
    @app.errorhandler(jwt_exceptions.NoAuthorizationError)
    def handle_no_authorization(e):
        """Обработка отсутствия JWT токена"""
        return jsonify({
            'error': 'Отсутствует токен авторизации'
        }), 401
    
    @app.errorhandler(jwt_exceptions.InvalidHeaderError)
    def handle_invalid_header(e):
        """Обработка неверного заголовка JWT"""
        return jsonify({
            'error': 'Неверный формат заголовка авторизации'
        }), 401
    
    @app.errorhandler(jwt_exceptions.ExpiredSignatureError)
    def handle_expired_token(e):
        """Обработка истекшего токена"""
        return jsonify({
            'error': 'Токен истек',
            'message': 'Пожалуйста, войдите снова'
        }), 401
    
    @app.errorhandler(jwt_exceptions.RevokedTokenError)
    def handle_revoked_token(e):
        """Обработка отозванного токена"""
        return jsonify({
            'error': 'Токен был отозван'
        }), 401
    
    @app.errorhandler(jwt_exceptions.FreshTokenRequired)
    def handle_fresh_token_required(e):
        """Обработка требования свежего токена"""
        return jsonify({
            'error': 'Требуется свежий токен',
            'message': 'Пожалуйста, войдите снова для выполнения этого действия'
        }), 401
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(e):
        """Обработка всех HTTP исключений"""
        return jsonify({
            'error': e.description or 'Произошла ошибка'
        }), e.code
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        """Обработка неожиданных ошибок"""
        app.logger.error(f'Unexpected error: {str(e)}')
        return jsonify({
            'error': 'Произошла непредвиденная ошибка'
        }), 500