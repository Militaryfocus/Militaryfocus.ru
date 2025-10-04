"""
Генератор sitemap.xml для SEO
"""
import os
from datetime import datetime
from flask import url_for
from blog.models import Post, Category
from blog.database import db

class SitemapGenerator:
    """Генератор карты сайта"""
    
    def __init__(self, base_url=None):
        self.base_url = base_url or os.environ.get('SITE_URL', 'https://militaryfocus.ru')
        
    def generate(self):
        """Генерирует sitemap.xml"""
        xml = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        # Главная страница
        xml.append(self._create_url_entry(
            self.base_url,
            changefreq='daily',
            priority='1.0'
        ))
        
        # Статические страницы
        static_pages = [
            ('/about', 'monthly', '0.5'),
            ('/contact', 'monthly', '0.5'),
            ('/search', 'monthly', '0.3'),
            ('/blog/', 'daily', '0.9'),
        ]
        
        for path, freq, priority in static_pages:
            xml.append(self._create_url_entry(
                self.base_url + path,
                changefreq=freq,
                priority=priority
            ))
        
        # Категории
        categories = Category.query.filter_by(is_active=True).all()
        for category in categories:
            xml.append(self._create_url_entry(
                f"{self.base_url}/blog/category/{category.slug}",
                changefreq='weekly',
                priority='0.8'
            ))
        
        # Посты
        posts = Post.query.filter_by(is_published=True).order_by(Post.published_at.desc()).all()
        for post in posts:
            xml.append(self._create_url_entry(
                f"{self.base_url}/blog/post/{post.slug}",
                lastmod=post.updated_at.strftime('%Y-%m-%d'),
                changefreq='monthly',
                priority='0.7'
            ))
        
        xml.append('</urlset>')
        return '\n'.join(xml)
    
    def _create_url_entry(self, loc, lastmod=None, changefreq='weekly', priority='0.5'):
        """Создает запись URL для sitemap"""
        entry = [f'  <url>']
        entry.append(f'    <loc>{loc}</loc>')
        
        if lastmod:
            entry.append(f'    <lastmod>{lastmod}</lastmod>')
        
        entry.append(f'    <changefreq>{changefreq}</changefreq>')
        entry.append(f'    <priority>{priority}</priority>')
        entry.append(f'  </url>')
        
        return '\n'.join(entry)
    
    def save_to_file(self, filepath='static/sitemap.xml'):
        """Сохраняет sitemap в файл"""
        content = self.generate()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath