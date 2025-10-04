"""
Таблицы связей many-to-many
"""

from blog import db

# Таблица связей постов и тегов
post_tags = db.Table('post_tags',
    db.Column('post_id', db.Integer, db.ForeignKey('posts.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True),
    db.Index('idx_post_tags_post', 'post_id'),
    db.Index('idx_post_tags_tag', 'tag_id')
)