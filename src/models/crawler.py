from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.extensions import db
import json

class CrawlJob(db.Model):
    __tablename__ = 'crawl_jobs'

    id = db.Column(db.Integer, primary_key=True)
    urls = db.Column(db.Text, nullable=False)  # JSON string of URLs
    max_depth = db.Column(db.Integer, default=3)
    status = db.Column(db.String(20), default='pending')  # pending, running, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    total_pages = db.Column(db.Integer, default=0)
    pdf_filename = db.Column(db.String(255))
    error_message = db.Column(db.Text)

    # Relationship to crawled pages
    pages = db.relationship('CrawledPage', backref='job', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'urls': json.loads(self.urls) if self.urls else [],
            'max_depth': self.max_depth,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_pages': self.total_pages,
            'pdf_filename': self.pdf_filename,
            'error_message': self.error_message
        }

class CrawledPage(db.Model):
    __tablename__ = 'crawled_pages'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('crawl_jobs.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text)
    content = db.Column(db.Text)
    videos = db.Column(db.Text)  # JSON string of video URLs
    depth = db.Column(db.Integer, default=0)
    crawled_at = db.Column(db.DateTime, default=datetime.utcnow)
    status_code = db.Column(db.Integer)
    error_message = db.Column(db.Text)

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'url': self.url,
            'title': self.title,
            'content': self.content,
            'videos': json.loads(self.videos) if self.videos else [],
            'depth': self.depth,
            'crawled_at': self.crawled_at.isoformat() if self.crawled_at else None,
            'status_code': self.status_code,
            'error_message': self.error_message
        }

