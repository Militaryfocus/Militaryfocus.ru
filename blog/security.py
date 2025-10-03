"""
Middleware для безопасных заголовков HTTP
"""

from flask import Flask, request, g
import time

def init_security_headers(app: Flask):
    """Инициализация безопасных заголовков"""
    
    @app.before_request
    def before_request():
        """Обработка запроса перед выполнением"""
        g.start_time = time.time()
    
    @app.after_request
    def after_request(response):
        """Добавление безопасных заголовков после обработки запроса"""
        
        # Заголовки безопасности
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers['Content-Security-Policy'] = csp
        
        # Strict Transport Security (только для HTTPS)
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Заголовки производительности
        if hasattr(g, 'start_time'):
            response.headers['X-Response-Time'] = f"{time.time() - g.start_time:.3f}s"
        
        # Заголовки кэширования для статических файлов
        if request.endpoint and request.endpoint.startswith('static'):
            response.headers['Cache-Control'] = 'public, max-age=31536000'
        
        return response