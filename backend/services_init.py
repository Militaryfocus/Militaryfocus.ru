"""
Инициализация всех сервисов приложения
"""
from flask import Flask
from services.core import (
    post_service, user_service, comment_service, 
    category_service, tag_service, notification_service,
    bookmark_service, view_service, like_service, session_service
)
from services.ai import (
    PerfectAIContentSystem, BiasMitigationSystem,
    ContentPersonalizationEngine, AdvancedContentGenerator,
    IntegratedContentManager, AIManager
)
from services.seo import (
    AdvancedSEOOptimizer, AutoSEOOptimizer, SEOAnalytics
)
from services.monitoring import MonitoringSystem
from services.error_detection import ErrorDetectionSystem

# Глобальные экземпляры сервисов
ai_content_system = None
bias_mitigation = None
content_personalization = None
advanced_generator = None
content_manager = None
ai_manager = None
seo_optimizer = None
auto_seo = None
seo_analytics = None
monitoring_system = None
error_detection = None

def init_services(app: Flask):
    """Инициализировать все сервисы"""
    global ai_content_system, bias_mitigation, content_personalization
    global advanced_generator, content_manager, ai_manager
    global seo_optimizer, auto_seo, seo_analytics
    global monitoring_system, error_detection
    
    with app.app_context():
        # AI сервисы
        ai_content_system = PerfectAIContentSystem()
        bias_mitigation = BiasMitigationSystem()
        content_personalization = ContentPersonalizationEngine()
        advanced_generator = AdvancedContentGenerator()
        content_manager = IntegratedContentManager()
        ai_manager = AIManager()
        
        # SEO сервисы
        seo_optimizer = AdvancedSEOOptimizer()
        auto_seo = AutoSEOOptimizer()
        seo_analytics = SEOAnalytics()
        
        # Системные сервисы
        monitoring_system = MonitoringSystem()
        error_detection = ErrorDetectionSystem()
        
        # Регистрация в приложении
        app.ai_content = ai_content_system
        app.bias_mitigation = bias_mitigation
        app.content_personalization = content_personalization
        app.advanced_generator = advanced_generator
        app.content_manager = content_manager
        app.ai_manager = ai_manager
        app.seo_optimizer = seo_optimizer
        app.auto_seo = auto_seo
        app.seo_analytics = seo_analytics
        app.monitoring = monitoring_system
        app.error_detection = error_detection
        
        print("✅ All services initialized successfully!")

def get_ai_service():
    """Получить AI сервис"""
    return ai_content_system

def get_seo_service():
    """Получить SEO сервис"""
    return seo_optimizer

def get_monitoring_service():
    """Получить сервис мониторинга"""
    return monitoring_system