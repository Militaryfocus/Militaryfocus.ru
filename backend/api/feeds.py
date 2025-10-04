"""
RSS и Atom feeds для блога
"""

from flask import Blueprint, Response, request, url_for
from models import Post, Category
from config.database import db
from datetime import datetime
import xml.etree.ElementTree as ET
from xml.dom import minidom

bp = Blueprint('feeds', __name__, url_prefix='/feeds')

@bp.route('/rss')
@bp.route('/rss/<category_slug>')
def rss_feed(category_slug=None):
    """Генерирует RSS feed"""
    # Базовый запрос
    query = Post.query.filter_by(is_published=True)
    
    # Фильтр по категории
    feed_title = "Блог - Все посты"
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)
        feed_title = f"Блог - {category.name}"
    
    # Получаем последние посты
    posts = query.order_by(Post.created_at.desc()).limit(20).all()
    
    # Создаем RSS XML
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    
    # Метаданные канала
    ET.SubElement(channel, 'title').text = feed_title
    ET.SubElement(channel, 'link').text = request.url_root
    ET.SubElement(channel, 'description').text = "Современный блог с интересными статьями"
    ET.SubElement(channel, 'language').text = 'ru'
    ET.SubElement(channel, 'copyright').text = f"© {datetime.now().year} МойБлог"
    ET.SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    
    # Добавляем посты
    for post in posts:
        item = ET.SubElement(channel, 'item')
        
        # Основные поля
        ET.SubElement(item, 'title').text = post.title
        ET.SubElement(item, 'link').text = url_for('blog.post_detail', slug=post.slug, _external=True)
        ET.SubElement(item, 'description').text = post.excerpt or post.get_excerpt(200)
        ET.SubElement(item, 'author').text = f"{post.author.email} ({post.author.username})"
        ET.SubElement(item, 'guid').text = url_for('blog.post_detail', slug=post.slug, _external=True)
        ET.SubElement(item, 'pubDate').text = post.created_at.strftime('%a, %d %b %Y %H:%M:%S GMT')
        
        # Категории
        if post.category:
            ET.SubElement(item, 'category').text = post.category.name
        
        # Теги
        for tag in post.tags:
            ET.SubElement(item, 'category').text = tag.name
    
    # Преобразуем в строку с форматированием
    xml_str = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
    
    return Response(pretty_xml, mimetype='application/rss+xml')

@bp.route('/atom')
@bp.route('/atom/<category_slug>')
def atom_feed(category_slug=None):
    """Генерирует Atom feed"""
    # Базовый запрос
    query = Post.query.filter_by(is_published=True)
    
    # Фильтр по категории
    feed_title = "Блог - Все посты"
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)
        feed_title = f"Блог - {category.name}"
    
    # Получаем последние посты
    posts = query.order_by(Post.created_at.desc()).limit(20).all()
    
    # Создаем Atom XML с namespace
    ATOM_NS = "http://www.w3.org/2005/Atom"
    feed = ET.Element('{%s}feed' % ATOM_NS)
    
    # Метаданные feed
    ET.SubElement(feed, '{%s}title' % ATOM_NS).text = feed_title
    ET.SubElement(feed, '{%s}id' % ATOM_NS).text = request.url_root
    ET.SubElement(feed, '{%s}updated' % ATOM_NS).text = datetime.utcnow().isoformat() + 'Z'
    
    link_self = ET.SubElement(feed, '{%s}link' % ATOM_NS)
    link_self.set('rel', 'self')
    link_self.set('href', request.url)
    
    link_alt = ET.SubElement(feed, '{%s}link' % ATOM_NS)
    link_alt.set('rel', 'alternate')
    link_alt.set('href', request.url_root)
    
    ET.SubElement(feed, '{%s}subtitle' % ATOM_NS).text = "Современный блог с интересными статьями"
    
    # Добавляем посты
    for post in posts:
        entry = ET.SubElement(feed, '{%s}entry' % ATOM_NS)
        
        ET.SubElement(entry, '{%s}title' % ATOM_NS).text = post.title
        ET.SubElement(entry, '{%s}id' % ATOM_NS).text = url_for('blog.post_detail', slug=post.slug, _external=True)
        ET.SubElement(entry, '{%s}updated' % ATOM_NS).text = post.updated_at.isoformat() + 'Z'
        ET.SubElement(entry, '{%s}published' % ATOM_NS).text = post.created_at.isoformat() + 'Z'
        
        link = ET.SubElement(entry, '{%s}link' % ATOM_NS)
        link.set('rel', 'alternate')
        link.set('href', url_for('blog.post_detail', slug=post.slug, _external=True))
        
        author = ET.SubElement(entry, '{%s}author' % ATOM_NS)
        ET.SubElement(author, '{%s}name' % ATOM_NS).text = post.author.username
        
        ET.SubElement(entry, '{%s}summary' % ATOM_NS).text = post.excerpt or post.get_excerpt(200)
        
        content = ET.SubElement(entry, '{%s}content' % ATOM_NS)
        content.set('type', 'html')
        content.text = post.content
        
        # Категории
        for tag in post.tags:
            category = ET.SubElement(entry, '{%s}category' % ATOM_NS)
            category.set('term', tag.name)
    
    # Преобразуем в строку
    ET.register_namespace('', ATOM_NS)
    xml_str = ET.tostring(feed, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding='utf-8')
    
    return Response(pretty_xml, mimetype='application/atom+xml')

@bp.route('/json')
@bp.route('/json/<category_slug>')
def json_feed(category_slug=None):
    """Генерирует JSON Feed (современный формат)"""
    from flask import jsonify
    
    # Базовый запрос
    query = Post.query.filter_by(is_published=True)
    
    # Фильтр по категории
    feed_title = "Блог - Все посты"
    if category_slug:
        category = Category.query.filter_by(slug=category_slug).first_or_404()
        query = query.filter_by(category_id=category.id)
        feed_title = f"Блог - {category.name}"
    
    # Получаем последние посты
    posts = query.order_by(Post.created_at.desc()).limit(20).all()
    
    # Формируем JSON Feed
    feed = {
        "version": "https://jsonfeed.org/version/1.1",
        "title": feed_title,
        "home_page_url": request.url_root,
        "feed_url": request.url,
        "description": "Современный блог с интересными статьями",
        "language": "ru",
        "icon": url_for('static', filename='images/favicon.ico', _external=True),
        "favicon": url_for('static', filename='images/favicon.ico', _external=True),
        "authors": [{
            "name": "МойБлог",
            "url": request.url_root
        }],
        "items": []
    }
    
    # Добавляем посты
    for post in posts:
        item = {
            "id": str(post.id),
            "url": url_for('blog.post_detail', slug=post.slug, _external=True),
            "title": post.title,
            "content_html": post.content,
            "content_text": post.get_text_content(),
            "summary": post.excerpt or post.get_excerpt(200),
            "date_published": post.created_at.isoformat() + 'Z',
            "date_modified": post.updated_at.isoformat() + 'Z',
            "authors": [{
                "name": post.author.username,
                "url": url_for('author_stats.author_stats', user_id=post.author.id, _external=True)
            }],
            "tags": [tag.name for tag in post.tags]
        }
        
        # Добавляем изображение если есть
        if post.image_url:
            item["image"] = post.image_url
            item["banner_image"] = post.image_url
        
        feed["items"].append(item)
    
    return jsonify(feed)

@bp.route('/sitemap.xml')
def sitemap():
    """Генерирует sitemap.xml"""
    from utils.sitemap_generator import SitemapGenerator
    
    generator = SitemapGenerator()
    xml_content = generator.generate()
    
    return Response(xml_content, mimetype='application/xml')

# Добавляем ссылки на feeds в заголовки страниц
def add_feed_links(response):
    """Добавляет auto-discovery ссылки на feeds"""
    if response.content_type and 'html' in response.content_type:
        # Добавляем ссылки перед </head>
        feed_links = '''
    <link rel="alternate" type="application/rss+xml" title="RSS Feed" href="/feeds/rss">
    <link rel="alternate" type="application/atom+xml" title="Atom Feed" href="/feeds/atom">
    <link rel="alternate" type="application/json" title="JSON Feed" href="/feeds/json">
        '''
        
        response_text = response.get_data(as_text=True)
        if '</head>' in response_text:
            response_text = response_text.replace('</head>', feed_links + '</head>')
            response.set_data(response_text)
    
    return response