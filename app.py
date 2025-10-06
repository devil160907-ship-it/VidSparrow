from venv import logger
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from authlib.integrations.flask_client import OAuth
import os
from models import db, User, Download
from utils.downloader import VideoDownloader
from utils.video_processor import VideoProcessor
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

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

@app.route('/get-enhanced-video-info', methods=['POST'])
def get_enhanced_video_info():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    data = request.get_json()
    url = data.get('url', '')
    platform = data.get('platform', '')
    
    if not url:
        return jsonify({'success': False, 'error': 'No URL provided'})
    
    try:
        # Validate URL first
        validation = VideoProcessor.validate_url(url, platform)
        if not validation['success']:
            return jsonify({'success': False, 'error': validation['error']})
        
        # Get basic video info
        video_info = VideoDownloader.get_video_info(url)
        if not video_info['success']:
            return jsonify(video_info)
        
        # Get enhanced metadata
        metadata = VideoProcessor.extract_metadata(url, platform)
        
        # Get available formats
        formats = VideoProcessor.get_available_formats(url, platform)
        
        response_data = {
            'success': True,
            'basic_info': video_info,
            'metadata': metadata,
            'available_formats': formats,
            'validation': validation
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download', methods=['POST'])
def download():
    if 'user' not in session:
        return jsonify({'success': False, 'error': 'Not authenticated'})
    
    data = request.get_json()
    url = data.get('url', '')
    platform = data.get('platform', '')
    media_type = data.get('media_type', '')
    quality = data.get('quality', 'best')  # Add quality parameter
    
    print(f"Download request - URL: {url}, Platform: {platform}, Media Type: {media_type}, Quality: {quality}")
    
    if not all([url, platform, media_type]):
        return jsonify({'success': False, 'error': 'Missing parameters'})
    
    try:
        # Enhanced URL validation
        validation = VideoProcessor.validate_url(url, platform)
        if not validation['success']:
            return jsonify({'success': False, 'error': validation['error']})
        
        print("Starting download process...")
        result = VideoDownloader.download_media(url, media_type, platform, quality)  # Pass quality parameter
        
        if result and result.get('success'):
            # Sanitize filename before saving to database
            sanitized_title = VideoProcessor.sanitize_filename(result['title'])
            
            # Save download record
            download = Download(
                user_id=session['user']['id'],
                platform=platform,
                media_type=media_type,
                video_url=url,
                video_title=sanitized_title,
                thumbnail_url=result['thumbnail']
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
                'sanitized_title': sanitized_title
            })
        else:
            error_msg = result.get('error', 'Download failed') if result else 'Download failed'
            print(f"Download failed: {error_msg}")
            return jsonify({'success': False, 'error': error_msg})
    except Exception as e:
        print(f"Download exception: {str(e)}")
        import traceback
        traceback.print_exc()
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