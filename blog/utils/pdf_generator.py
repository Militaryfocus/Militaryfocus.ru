"""
Генератор PDF для экспорта постов
"""

import os
from io import BytesIO
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bs4 import BeautifulSoup
import re

class PDFGenerator:
    """Генератор PDF документов"""
    
    def __init__(self, pagesize=A4):
        self.pagesize = pagesize
        self.styles = getSampleStyleSheet()
        self._setup_styles()
        
    def _setup_styles(self):
        """Настройка стилей для PDF"""
        # Заголовок документа
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Метаинформация
        self.styles.add(ParagraphStyle(
            name='Meta',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#666666'),
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Основной текст
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
        
        # Заголовки разделов
        self.styles.add(ParagraphStyle(
            name='CustomHeading2',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#2c3e50'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        # Цитаты
        self.styles.add(ParagraphStyle(
            name='Blockquote',
            parent=self.styles['Normal'],
            fontSize=10,
            leftIndent=20,
            rightIndent=20,
            textColor=colors.HexColor('#555555'),
            fontName='Helvetica-Oblique',
            borderColor=colors.HexColor('#cccccc'),
            borderWidth=1,
            borderPadding=10,
            backColor=colors.HexColor('#f9f9f9')
        ))
    
    def generate_post_pdf(self, post):
        """
        Генерирует PDF для одного поста
        
        Args:
            post: Объект поста
            
        Returns:
            BytesIO объект с PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Заголовок
        story.append(Paragraph(post.title, self.styles['CustomTitle']))
        
        # Метаинформация
        meta_text = f"Автор: {post.author.username} | "
        meta_text += f"Дата: {post.created_at.strftime('%d.%m.%Y')} | "
        if post.category:
            meta_text += f"Категория: {post.category.name}"
        story.append(Paragraph(meta_text, self.styles['Meta']))
        story.append(Spacer(1, 0.2*inch))
        
        # Excerpt если есть
        if post.excerpt:
            story.append(Paragraph(f"<i>{post.excerpt}</i>", self.styles['CustomBody']))
            story.append(Spacer(1, 0.2*inch))
        
        # Основной контент
        content_parts = self._process_html_content(post.content)
        for part in content_parts:
            story.append(part)
        
        # Теги
        if post.tags:
            story.append(Spacer(1, 0.3*inch))
            tags_text = "Теги: " + ", ".join([tag.name for tag in post.tags])
            story.append(Paragraph(tags_text, self.styles['Meta']))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"© {datetime.now().year} {post.author.username}. "
        footer_text += f"Оригинал: {post.get_absolute_url()}"
        story.append(Paragraph(footer_text, self.styles['Meta']))
        
        # Генерируем PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        buffer.seek(0)
        return buffer
    
    def generate_posts_collection_pdf(self, posts, title="Коллекция постов"):
        """
        Генерирует PDF с несколькими постами
        
        Args:
            posts: Список постов
            title: Заголовок коллекции
            
        Returns:
            BytesIO объект с PDF
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=self.pagesize,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        story = []
        
        # Титульная страница
        story.append(Spacer(1, 2*inch))
        story.append(Paragraph(title, self.styles['CustomTitle']))
        story.append(Spacer(1, 0.5*inch))
        story.append(Paragraph(
            f"Всего постов: {len(posts)}", 
            self.styles['Meta']
        ))
        story.append(Paragraph(
            f"Дата создания: {datetime.now().strftime('%d.%m.%Y %H:%M')}", 
            self.styles['Meta']
        ))
        story.append(PageBreak())
        
        # Оглавление
        story.append(Paragraph("Содержание", self.styles['CustomTitle']))
        story.append(Spacer(1, 0.3*inch))
        
        toc_data = []
        for i, post in enumerate(posts, 1):
            toc_data.append([
                str(i),
                post.title,
                post.author.username,
                post.created_at.strftime('%d.%m.%Y')
            ])
        
        toc_table = Table(toc_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch, 1*inch])
        toc_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(toc_table)
        story.append(PageBreak())
        
        # Посты
        for i, post in enumerate(posts):
            if i > 0:
                story.append(PageBreak())
            
            # Заголовок поста
            story.append(Paragraph(post.title, self.styles['CustomTitle']))
            
            # Метаинформация
            meta_text = f"Автор: {post.author.username} | "
            meta_text += f"Дата: {post.created_at.strftime('%d.%m.%Y')}"
            if post.category:
                meta_text += f" | Категория: {post.category.name}"
            story.append(Paragraph(meta_text, self.styles['Meta']))
            story.append(Spacer(1, 0.2*inch))
            
            # Контент
            if post.excerpt:
                story.append(Paragraph(f"<i>{post.excerpt}</i>", self.styles['CustomBody']))
                story.append(Spacer(1, 0.2*inch))
            
            content_parts = self._process_html_content(post.content)
            for part in content_parts:
                story.append(part)
        
        # Генерируем PDF
        doc.build(story, onFirstPage=self._add_page_number, onLaterPages=self._add_page_number)
        
        buffer.seek(0)
        return buffer
    
    def _process_html_content(self, html_content):
        """
        Обрабатывает HTML контент для PDF
        
        Args:
            html_content: HTML строка
            
        Returns:
            Список элементов для PDF
        """
        story = []
        
        # Очищаем HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Удаляем скрипты и стили
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Обрабатываем элементы
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'blockquote', 'ul', 'ol']):
            if element.name == 'p':
                text = element.get_text(strip=True)
                if text:
                    story.append(Paragraph(text, self.styles['CustomBody']))
            
            elif element.name in ['h1', 'h2', 'h3', 'h4']:
                text = element.get_text(strip=True)
                if text:
                    story.append(Paragraph(text, self.styles['CustomHeading2']))
            
            elif element.name == 'blockquote':
                text = element.get_text(strip=True)
                if text:
                    story.append(Paragraph(text, self.styles['Blockquote']))
                    story.append(Spacer(1, 0.1*inch))
            
            elif element.name in ['ul', 'ol']:
                items = []
                for li in element.find_all('li'):
                    text = li.get_text(strip=True)
                    if text:
                        if element.name == 'ul':
                            items.append(f"• {text}")
                        else:
                            items.append(f"{len(items) + 1}. {text}")
                
                if items:
                    for item in items:
                        story.append(Paragraph(item, self.styles['CustomBody']))
        
        return story
    
    def _add_page_number(self, canvas, doc):
        """Добавляет номер страницы"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.HexColor('#999999'))
        
        page_num = canvas.getPageNumber()
        text = f"Страница {page_num}"
        
        canvas.drawCentredString(
            doc.pagesize[0] / 2,
            0.75 * inch,
            text
        )
        canvas.restoreState()


# Простая альтернатива без внешних зависимостей
class SimplePDFGenerator:
    """Простой генератор PDF используя только HTML"""
    
    @staticmethod
    def generate_html_for_pdf(post):
        """Генерирует HTML для конвертации в PDF"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>{post.title}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                }}
                .meta {{
                    color: #7f8c8d;
                    font-size: 14px;
                    margin-bottom: 20px;
                }}
                .content {{
                    text-align: justify;
                }}
                .tags {{
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ecf0f1;
                    color: #7f8c8d;
                }}
                @media print {{
                    body {{
                        margin: 0;
                        padding: 10px;
                    }}
                }}
            </style>
        </head>
        <body>
            <h1>{post.title}</h1>
            <div class="meta">
                Автор: {post.author.username} | 
                Дата: {post.created_at.strftime('%d.%m.%Y')} | 
                Категория: {post.category.name if post.category else 'Без категории'}
            </div>
            <div class="content">
                {post.content}
            </div>
            <div class="tags">
                Теги: {', '.join([tag.name for tag in post.tags]) if post.tags else 'Нет тегов'}
            </div>
        </body>
        </html>
        """
        return html