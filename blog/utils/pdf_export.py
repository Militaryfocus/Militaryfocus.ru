"""
Экспорт постов в PDF
"""
import os
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from html.parser import HTMLParser
import re

class HTMLStripper(HTMLParser):
    """Простой парсер для удаления HTML тегов"""
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = []
    
    def handle_data(self, data):
        self.text.append(data)
    
    def get_text(self):
        return ''.join(self.text)

def strip_html(html):
    """Удаляет HTML теги из текста"""
    s = HTMLStripper()
    s.feed(html)
    return s.get_text()

class PDFExporter:
    """Класс для экспорта постов в PDF"""
    
    def __init__(self, pagesize=A4):
        self.pagesize = pagesize
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Настройка стилей для PDF"""
        # Заголовок документа
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Заголовок поста
        self.styles.add(ParagraphStyle(
            name='PostTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        ))
        
        # Метаинформация
        self.styles.add(ParagraphStyle(
            name='Meta',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=12
        ))
        
        # Основной текст
        self.styles.add(ParagraphStyle(
            name='PostBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
    
    def export_post(self, post):
        """Экспортирует один пост в PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        story = []
        
        # Логотип/заголовок
        story.append(Paragraph("Military Focus Blog", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Заголовок поста
        story.append(Paragraph(post.title, self.styles['PostTitle']))
        
        # Метаинформация
        meta_info = f"Автор: {post.author.username} | Дата: {post.created_at.strftime('%d.%m.%Y')} | Категория: {post.category.name if post.category else 'Без категории'}"
        story.append(Paragraph(meta_info, self.styles['Meta']))
        
        # Теги
        if post.tags:
            tags_text = "Теги: " + ", ".join([tag.name for tag in post.tags])
            story.append(Paragraph(tags_text, self.styles['Meta']))
        
        story.append(Spacer(1, 0.3*inch))
        
        # Контент поста (упрощенный, без HTML)
        content = strip_html(post.content)
        # Разбиваем на параграфы
        paragraphs = content.split('\n\n')
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), self.styles['PostBody']))
        
        # Статистика
        story.append(Spacer(1, 0.5*inch))
        stats_data = [
            ['Просмотры:', str(post.views)],
            ['Комментарии:', str(len(post.comments))],
            ['Лайки:', str(post.get_likes_count() if hasattr(post, 'get_likes_count') else 0)]
        ]
        
        stats_table = Table(stats_data, colWidths=[2*inch, 1*inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.gray)
        ]))
        
        story.append(stats_table)
        
        # Генерируем PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    def export_multiple_posts(self, posts, title="Сборник постов"):
        """Экспортирует несколько постов в один PDF"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=self.pagesize,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        story = []
        
        # Титульная страница
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(f"Всего постов: {len(posts)}", self.styles['Meta']))
        story.append(Paragraph(f"Дата создания: {datetime.now().strftime('%d.%m.%Y')}", self.styles['Meta']))
        story.append(PageBreak())
        
        # Оглавление
        story.append(Paragraph("Оглавление", self.styles['Heading1']))
        story.append(Spacer(1, 0.3*inch))
        
        toc_data = []
        for i, post in enumerate(posts, 1):
            toc_data.append([
                f"{i}.",
                post.title[:60] + "..." if len(post.title) > 60 else post.title,
                post.created_at.strftime('%d.%m.%Y')
            ])
        
        toc_table = Table(toc_data, colWidths=[0.5*inch, 4.5*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
        ]))
        
        story.append(toc_table)
        story.append(PageBreak())
        
        # Посты
        for i, post in enumerate(posts):
            # Заголовок поста
            story.append(Paragraph(f"{i+1}. {post.title}", self.styles['PostTitle']))
            
            # Метаинформация
            meta_info = f"Автор: {post.author.username} | Дата: {post.created_at.strftime('%d.%m.%Y')}"
            story.append(Paragraph(meta_info, self.styles['Meta']))
            
            story.append(Spacer(1, 0.2*inch))
            
            # Контент (упрощенный)
            content = strip_html(post.content)
            # Ограничиваем длину контента
            if len(content) > 3000:
                content = content[:3000] + "..."
            
            paragraphs = content.split('\n\n')
            for para in paragraphs[:5]:  # Максимум 5 параграфов
                if para.strip():
                    story.append(Paragraph(para.strip(), self.styles['PostBody']))
            
            # Разделитель между постами
            if i < len(posts) - 1:
                story.append(Spacer(1, 0.3*inch))
                story.append(Paragraph("* * *", self.styles['Meta']))
                story.append(Spacer(1, 0.3*inch))
            else:
                story.append(PageBreak())
        
        # Финальная страница
        story.append(Paragraph("Конец документа", self.styles['Meta']))
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph(f"Экспортировано с Military Focus Blog", self.styles['Meta']))
        story.append(Paragraph(f"{datetime.now().strftime('%d.%m.%Y %H:%M')}", self.styles['Meta']))
        
        # Генерируем PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer

# Простая функция для быстрого экспорта
def export_post_to_pdf(post):
    """Быстрый экспорт одного поста в PDF"""
    exporter = PDFExporter()
    return exporter.export_post(post)

def export_posts_to_pdf(posts, title="Сборник постов"):
    """Быстрый экспорт нескольких постов в PDF"""
    exporter = PDFExporter()
    return exporter.export_multiple_posts(posts, title)