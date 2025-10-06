from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    google_id = db.Column(db.String(255), unique=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    profile_pic = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with downloads
    downloads = db.relationship('Download', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'google_id': self.google_id,
            'email': self.email,
            'name': self.name,
            'profile_pic': self.profile_pic,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Download(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(50), nullable=False)  # youtube, instagram, etc.
    media_type = db.Column(db.String(10), nullable=False)  # mp4, mp3
    video_url = db.Column(db.Text, nullable=False)
    video_title = db.Column(db.Text, nullable=False)
    thumbnail_url = db.Column(db.Text)
    downloaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'platform': self.platform,
            'media_type': self.media_type,
            'video_url': self.video_url,
            'video_title': self.video_title,
            'thumbnail_url': self.thumbnail_url,
            'downloaded_at': self.downloaded_at.isoformat() if self.downloaded_at else None
        }
    
    @staticmethod
    def delete_download(download_id, user_id):
        """Delete a download record by ID if it belongs to the user"""
        download = Download.query.filter_by(id=download_id, user_id=user_id).first()
        if download:
            db.session.delete(download)
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def delete_all_user_downloads(user_id):
        """Delete all download records for a user"""
        downloads = Download.query.filter_by(user_id=user_id).all()
        for download in downloads:
            db.session.delete(download)
        db.session.commit()
        return len(downloads)