from venv import logger
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from authlib.integrations.flask_client import OAuth
from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, session
from sqlalchemy import func
from datetime import datetime, timedelta
from models import db, User, Download

import os
from models import db, User, Download
from utils.downloader import VideoDownloader
from utils.video_processor import VideoProcessor
from config import Config
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Custom formatters
def file_size_formatter(view, value):
    if value:
        if value < 1024:
            return f"{value} B"
        elif value < 1024 * 1024:
            return f"{value/1024:.1f} KB"
        elif value < 1024 * 1024 * 1024:
            return f"{value/(1024*1024):.1f} MB"
        else:
            return f"{value/(1024*1024*1024):.1f} GB"
    return "N/A"

def datetime_formatter(view, value):
    if value:
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return "N/A"

def format_duration(view, value):
    if value:
        if isinstance(value, int):
            minutes, seconds = divmod(value, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        return str(value)
    return "N/A"

# Custom Admin Views
class UserAdminView(ModelView):
    column_list = ['id', 'name', 'email', 'download_count', 'created_at']
    column_searchable_list = ['email', 'name']
    column_filters = ['created_at']
    column_formatters = {
        'created_at': datetime_formatter,
        'download_count': lambda v, c, m, n: len(m.downloads)
    }
    page_size = 20
    
    def is_accessible(self):
        return 'user' in session
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class DownloadAdminView(ModelView):
    column_list = [
        'id', 'user_id', 'user_name', 'platform', 'media_type', 'format_type', 
        'video_title', 'file_size', 'duration', 'quality', 'download_status', 'downloaded_at'
    ]
    column_searchable_list = ['video_title', 'video_url']
    column_filters = [
        'platform', 'media_type', 'format_type', 'quality', 
        'download_status', 'downloaded_at'
    ]
    column_formatters = {
        'downloaded_at': datetime_formatter,
        'file_size': file_size_formatter,
        'duration': format_duration,
    }
    page_size = 50
    
    column_labels = {
        'format_type': 'Format',
        'download_status': 'Status',
        'file_size': 'File Size',
        'duration': 'Duration',
        'user_name': 'User Name'
    }
    
    def is_accessible(self):
        return 'user' in session
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import redirect, url_for, session
from sqlalchemy import func
from datetime import datetime, timedelta
from models import db, User, Download

# Custom Admin Views without the cls parameter issue
class SecureModelView(ModelView):
    def is_accessible(self):
        return 'user' in session
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

class UserAdminView(SecureModelView):
    column_list = ['id', 'name', 'email', 'created_at', 'download_count']
    column_searchable_list = ['email', 'name']
    column_filters = ['created_at']
    page_size = 20
    
    def get_query(self):
        return self.session.query(self.model)
    
    def get_count_query(self):
        return self.session.query(db.func.count(self.model.id))
    
    @expose('/')
    def index_view(self):
        return super().index_view()

class DownloadAdminView(SecureModelView):
    column_list = [
        'id', 'user_id', 'platform', 'media_type', 'format_type', 
        'video_title', 'file_size', 'quality', 'download_status', 'downloaded_at'
    ]
    column_searchable_list = ['video_title', 'video_url']
    column_filters = [
        'platform', 'media_type', 'format_type', 'quality', 
        'download_status', 'downloaded_at'
    ]
    page_size = 50
    
    @expose('/')
    def index_view(self):
        return super().index_view()

class StatsView(BaseView):
    @expose('/')
    def index(self):
        try:
            # Get total statistics
            total_users = User.query.count()
            total_downloads = Download.query.count()
            
            # Get downloads by format
            format_stats = db.session.query(
                Download.format_type,
                func.count(Download.id).label('count'),
                func.sum(Download.file_size).label('total_size')
            ).group_by(Download.format_type).all()
            
            # Get downloads by platform
            platform_stats = db.session.query(
                Download.platform,
                func.count(Download.id).label('count')
            ).group_by(Download.platform).all()
            
            # Get downloads by media type
            media_type_stats = db.session.query(
                Download.media_type,
                func.count(Download.id).label('count')
            ).group_by(Download.media_type).all()
            
            # Get recent downloads (last 10)
            recent_downloads = Download.query.order_by(Download.downloaded_at.desc()).limit(10).all()
            
            # Get top users by download count
            top_users = db.session.query(
                User.name,
                User.email,
                func.count(Download.id).label('download_count')
            ).join(Download, User.id == Download.user_id).group_by(User.id, User.name, User.email).order_by(func.count(Download.id).desc()).limit(10).all()
            
            # Get failed downloads count
            failed_downloads = Download.query.filter_by(download_status='failed').count()
            
            # Get today's downloads
            today = datetime.utcnow().date()
            today_downloads = Download.query.filter(
                func.date(Download.downloaded_at) == today
            ).count()
            
            # Get downloads from last 7 days
            last_week = datetime.utcnow() - timedelta(days=7)
            weekly_downloads = Download.query.filter(
                Download.downloaded_at >= last_week
            ).count()
            
            # Get most popular format
            most_popular_format = db.session.query(
                Download.format_type,
                func.count(Download.id).label('count')
            ).group_by(Download.format_type).order_by(func.count(Download.id).desc()).first()
            
            # Get most active platform
            most_active_platform = db.session.query(
                Download.platform,
                func.count(Download.id).label('count')
            ).group_by(Download.platform).order_by(func.count(Download.id).desc()).first()
            
            # Get average file size
            avg_file_size = db.session.query(
                func.avg(Download.file_size)
            ).filter(Download.file_size.isnot(None)).scalar()
            
            # Calculate success rate
            success_count = total_downloads - failed_downloads
            success_rate = (success_count / total_downloads * 100) if total_downloads > 0 else 0
            
            return self.render(
                'admin/stats.html',
                total_users=total_users,
                total_downloads=total_downloads,
                format_stats=format_stats,
                platform_stats=platform_stats,
                media_type_stats=media_type_stats,
                recent_downloads=recent_downloads,
                top_users=top_users,
                failed_downloads=failed_downloads,
                today_downloads=today_downloads,
                weekly_downloads=weekly_downloads,
                most_popular_format=most_popular_format,
                most_active_platform=most_active_platform,
                avg_file_size=avg_file_size,
                success_count=success_count,
                success_rate=success_rate,
                current_time=datetime.utcnow()
            )
            
        except Exception as e:
            print(f"Error in StatsView: {str(e)}")
            return f"Error loading statistics: {str(e)}"

    def is_accessible(self):
        return 'user' in session

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
    
def file_size_formatter(value):
    if value:
        if value < 1024:
            return f"{value} B"
        elif value < 1024 * 1024:
            return f"{value/1024:.1f} KB"
        elif value < 1024 * 1024 * 1024:
            return f"{value/(1024*1024):.1f} MB"
        else:
            return f"{value/(1024*1024*1024):.1f} GB"
    return "N/A"

def datetime_formatter(value):
    if value:
        return value.strftime('%Y-%m-%d %H:%M:%S')
    return "N/A"

def format_duration(value):
    if value:
        if isinstance(value, int):
            minutes, seconds = divmod(value, 60)
            hours, minutes = divmod(minutes, 60)
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        return str(value)
    return "N/A"

# Flask-Admin setup
admin = Admin(app, name='Video Downloader Admin', template_mode='bootstrap3', url='/admin')

# Add views to admin - use the correct endpoint names
admin.add_view(UserAdminView(User, db.session, name='Users', category='Management'))
admin.add_view(DownloadAdminView(Download, db.session, name='Downloads', category='Management'))
admin.add_view(StatsView(name='Statistics', endpoint='stats', category='Analytics'))

# OAuth configuration
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url=app.config['GOOGLE_DISCOVERY_URL'],
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Create tables within app context
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', user=session['user'])

@app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/google-login')
def google_login():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/google-callback')
def google_callback():
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            # Check if user exists
            user = User.query.filter_by(google_id=user_info['sub']).first()
            if not user:
                user = User(
                    google_id=user_info['sub'],
                    email=user_info['email'],
                    name=user_info['name'],
                    profile_pic=user_info['picture']
                )
                db.session.add(user)
                db.session.commit()
            
            session['user'] = {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'profile_pic': user.profile_pic
            }
            session.permanent = True
            
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    except Exception as e:
        print(f"Google callback error: {e}")
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/get-video-info', methods=['POST'])
def get_video_info():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'})
    
    url = data.get('url', '').strip()
    platform = data.get('platform', '')
    
    print(f"Received request - URL: {url}, Platform: {platform}")
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    try:
        # Enhanced URL validation with better error messages
        validation = VideoProcessor.validate_url(url, platform)
        if not validation['success']:
            error_msg = validation.get('error', 'Invalid URL')
            print(f"URL validation failed: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
        
        print("URL validation passed, getting video info...")
        
        # Get video info using yt-dlp
        video_info = VideoDownloader.get_video_info(url)
        
        print(f"Video info result: {video_info}")
        
        if not video_info['success']:
            error_msg = video_info.get('error', 'Failed to fetch video information')
            
            # Common yt-dlp errors and their user-friendly messages
            if 'Private video' in error_msg:
                error_msg = 'This video is private and cannot be downloaded.'
            elif 'Video unavailable' in error_msg:
                error_msg = 'This video is unavailable. It may have been removed or made private.'
            elif 'Sign in to confirm' in error_msg:
                error_msg = 'This video is age-restricted and cannot be downloaded.'
            elif 'Unsupported URL' in error_msg:
                error_msg = 'This URL is not supported. Please check if it\'s a valid YouTube or Instagram URL.'
            elif 'No video formats found' in error_msg:
                error_msg = 'No downloadable content found at this URL.'
            
            print(f"Video info error: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
        
        return jsonify(video_info)
        
    except Exception as e:
        print(f"Error in get-video-info: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': 'An unexpected error occurred. Please try again.'})

@app.route('/download', methods=['POST'])
def download():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    data = request.get_json()
    url = data.get('url', '')
    platform = data.get('platform', '')
    media_type = data.get('media_type', '')
    quality = data.get('quality', 'best')
    format_type = data.get('format_type', 'mp4')
    
    print(f"Download request - URL: {url}, Platform: {platform}, Media Type: {media_type}, Quality: {quality}, Format: {format_type}")
    
    if not all([url, platform, media_type]):
        return jsonify({'success': False, 'error': 'Missing parameters'})
    
    try:
        # Enhanced URL validation
        validation = VideoProcessor.validate_url(url, platform)
        if not validation['success']:
            return jsonify({'success': False, 'error': validation['error']})
        
        print("Starting download process...")
        result = VideoDownloader.download_media(url, media_type, platform, quality, format_type)
        
        if result and result.get('success'):
            # Sanitize filename before saving to database
            sanitized_title = VideoProcessor.sanitize_filename(result['title'])
            
            # Save download record with enhanced information
            download = Download(
                user_id=session['user']['id'],
                platform=platform,
                media_type=media_type,
                format_type=format_type,
                video_url=url,
                video_title=sanitized_title,
                thumbnail_url=result.get('thumbnail', ''),
                quality=quality,
                duration=result.get('duration', 0),
                file_size=result.get('file_size', 0),
                filename=result.get('filename', ''),
                download_status='completed'
            )
            db.session.add(download)
            db.session.commit()
            
            # Get file stats
            filepath = os.path.join('downloads', result['filename'])
            file_size = VideoProcessor.get_file_size(filepath)
            
            print(f"Download successful: {result['filename']}")
            
            return jsonify({
                'success': True,
                'filename': result['filename'],
                'title': result['title'],
                'file_size': file_size,
                'sanitized_title': sanitized_title,
                'format_type': format_type,
                'duration': result.get('duration', 0)
            })
        else:
            error_msg = result.get('error', 'Download failed') if result else 'Download failed'
            
            # Save failed download record
            download = Download(
                user_id=session['user']['id'],
                platform=platform,
                media_type=media_type,
                format_type=format_type,
                video_url=url,
                video_title=f"Failed: {url}",
                download_status='failed',
                error_message=error_msg
            )
            db.session.add(download)
            db.session.commit()
            
            print(f"Download failed: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
    except Exception as e:
        print(f"Download exception: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Save failed download record
        try:
            download = Download(
                user_id=session['user']['id'],
                platform=platform,
                media_type=media_type,
                format_type=format_type,
                video_url=url,
                video_title=f"Error: {url}",
                download_status='failed',
                error_message=str(e)
            )
            db.session.add(download)
            db.session.commit()
        except:
            pass
            
        return jsonify({'success': False, 'error': f'Download error: {str(e)}'})

@app.route('/download-file/<filename>')
def download_file(filename):
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Secure file path validation
    safe_filepath, error = VideoProcessor.validate_download_path(filename, 'downloads')
    if error:
        return "File not found", 404
    
    if os.path.exists(safe_filepath):
        return send_file(safe_filepath, as_attachment=True)
    else:
        return "File not found", 404
    
@app.route('/delete-download/<download_id>', methods=['DELETE'])
def delete_download(download_id):
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        if Download.delete_download(download_id, session['user']['id']):
            return jsonify({'success': True, 'message': 'Download deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Download not found or access denied'}), 404
    except Exception as e:
        logger.error(f"Delete download error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/clear-all-downloads', methods=['DELETE'])
def clear_all_downloads():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'}), 401
    
    try:
        count = Download.delete_all_user_downloads(session['user']['id'])
        return jsonify({'success': True, 'message': f'All {count} downloads cleared successfully'})
    except Exception as e:
        logger.error(f"Clear all downloads error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_downloads = Download.query.filter_by(user_id=session['user']['id'])\
        .order_by(Download.downloaded_at.desc()).all()
    
    # Generate download report
    download_report = VideoProcessor.generate_download_report(user_downloads)
    
    return render_template('profile.html', 
                         user=session['user'],
                         downloads=user_downloads,
                         report=download_report)

@app.route('/api/downloads')
def get_downloads():
    if 'user' not in session:
        return jsonify([])
    
    user_downloads = Download.query.filter_by(user_id=session['user']['id'])\
        .order_by(Download.downloaded_at.desc()).limit(50).all()
    
    return jsonify([download.to_dict() for download in user_downloads])

@app.route('/admin/cleanup', methods=['POST'])
def cleanup_files():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        VideoProcessor.cleanup_old_files(max_age_hours=24)
        stats = VideoProcessor.get_download_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/stats')
def get_stats():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    try:
        stats = VideoProcessor.get_download_stats()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Debug route for URL testing
@app.route('/debug-url', methods=['POST'])
def debug_url():
    """Debug endpoint to test URL validation"""
    data = request.get_json()
    url = data.get('url', '')
    platform = data.get('platform', 'youtube')
    
    if not url:
        return jsonify({'error': 'No URL provided'})
    
    # Test YouTube URL extraction and validation
    if platform == 'youtube':
        video_id = VideoProcessor._extract_youtube_id(url)
        validation = VideoProcessor._validate_youtube_url(url)
        return jsonify({
            'url': url,
            'platform': platform,
            'video_id': video_id,
            'validation': validation
        })
    else:
        validation = VideoProcessor.validate_url(url, platform)
        return jsonify({
            'url': url,
            'platform': platform,
            'validation': validation
        })

if __name__ == '__main__':
    # Create downloads directory if it doesn't exist
    os.makedirs('downloads', exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
