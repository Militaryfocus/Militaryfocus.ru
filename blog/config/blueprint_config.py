"""
Конфигурация Blueprint'ов
"""

from blog.routes.main import bp as main_bp
from blog.routes.auth import bp as auth_bp
from blog.routes.blog import bp as blog_bp
from blog.routes.admin import bp as admin_bp
from blog.routes.ai_admin import bp as ai_admin_bp
from blog.routes.system_admin import bp as system_admin_bp
from blog.routes.seo import bp as seo_bp
from blog.routes.api import api_bp

class BlueprintConfig:
    """Конфигурация Blueprint'ов"""
    
    @staticmethod
    def register_blueprints(app):
        """Регистрация всех Blueprint'ов"""
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp, url_prefix='/auth')
        app.register_blueprint(blog_bp, url_prefix='/blog')
        app.register_blueprint(admin_bp, url_prefix='/admin', name='blog_admin')
        app.register_blueprint(ai_admin_bp, url_prefix='/ai')
        app.register_blueprint(system_admin_bp, url_prefix='/system')
        app.register_blueprint(seo_bp)
        app.register_blueprint(api_bp)