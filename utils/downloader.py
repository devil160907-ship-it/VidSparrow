import platform
import yt_dlp
import os
import logging
import random

logger = logging.getLogger(__name__)

class VideoDownloader:
    @staticmethod
    def get_ydl_opts(media_type, download_dir='downloads', quality='best'):
        """Get yt-dlp options with enhanced configuration and quality support"""
        
        # Rotating User-Agents to avoid detection
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        common_headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }
        
        base_opts = {
            'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
            'http_headers': common_headers,
            # Throttle to avoid rate limiting
            'ratelimit': 5000000,  # 5 MB/s
            'retries': 10,
            'fragment_retries': 10,
            'skip_unavailable_fragments': True,
            'continue_dl': True,
            # YouTube specific
            'youtube_include_dash_manifest': False,
            'youtube_include_hls_manifest': False,
        }
        
        if media_type == 'mp3':
            # Audio quality settings
            if quality == 'best':
                audio_quality = '320'
            elif quality == '192k':
                audio_quality = '192'
            elif quality == '128k':
                audio_quality = '128'
            else:  # 64k or default
                audio_quality = '64'
                
            base_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }],
            })
        else:  # mp4 - Video quality settings
            if quality == 'best':
                format_spec = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            elif quality == '1080p':
                format_spec = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
            elif quality == '720p':
                format_spec = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
            elif quality == '480p':
                format_spec = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
            elif quality == '360p':
                format_spec = 'bestvideo[height<=360]+bestaudio/best[height<=360]'
            else:
                format_spec = 'bestvideo+bestaudio/best'
            
            base_opts.update({
                'format': format_spec,
                'merge_output_format': 'mp4',
            })
        
        return base_opts

@staticmethod
def get_video_info(url):
    """Get video information for preview including available formats"""
    try:
        print(f"Attempting to fetch info for URL: {url}")
        
        ydl_opts = {
            'quiet': False,  # Set to False for debugging
            'no_warnings': False,
            'extract_flat': False,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("YoutubeDL instance created, extracting info...")
            info = ydl.extract_info(url, download=False)
            print(f"Successfully extracted info: {info.get('title', 'Unknown')}")
        
        # Add platform-specific options if needed
        if platform == 'instagram':
            ydl_opts.update({
                'extract_flat': True
            })
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Extract available formats
            video_formats = []
            audio_formats = []
            
            if 'formats' in info:
                for fmt in info['formats']:
                    format_info = {
                        'format_id': fmt.get('format_id', 'unknown'),
                        'ext': fmt.get('ext', 'unknown'),
                        'quality': fmt.get('format_note', 'unknown'),
                        'filesize': fmt.get('filesize'),
                        'vcodec': fmt.get('vcodec', 'none'),
                        'acodec': fmt.get('acodec', 'none'),
                        'height': fmt.get('height'),
                        'width': fmt.get('width'),
                        'fps': fmt.get('fps')
                    }
                    
                    # Categorize as video or audio
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':
                        video_formats.append(format_info)
                    elif fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        audio_formats.append(format_info)
            
            return {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': info.get('duration', 0),
                'uploader': info.get('uploader', 'Unknown'),
                'view_count': info.get('view_count', 0),
                'video_formats': video_formats,
                'audio_formats': audio_formats,
                'success': True
            }
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {'success': False, 'error': str(e)}
    
    @staticmethod
    def download_media(url, media_type, platform, quality='best'):
        """Download media with specified quality and return file path"""
        try:
            logger.info(f"Starting download - URL: {url}, Type: {media_type}, Platform: {platform}, Quality: {quality}")
            
            if platform == 'youtube':
                return VideoDownloader._download_youtube_enhanced(url, media_type, quality)
            elif platform == 'instagram':
                return VideoDownloader._download_instagram(url, media_type, quality)
            else:
                return {'success': False, 'error': f'Unsupported platform: {platform}'}
        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def _download_youtube_enhanced(url, media_type, quality):
        """Enhanced YouTube download with multiple fallback methods and quality support"""
        download_dir = 'downloads'
        os.makedirs(download_dir, exist_ok=True)
        
        # Try method 1: Standard download with quality
        result = VideoDownloader._try_download_method_1(url, media_type, download_dir, quality)
        if result.get('success'):
            return result
        
        # Try method 2: Alternative format selection
        result = VideoDownloader._try_download_method_2(url, media_type, download_dir, quality)
        if result.get('success'):
            return result
        
        # Try method 3: Simple format
        result = VideoDownloader._try_download_method_3(url, media_type, download_dir, quality)
        if result.get('success'):
            return result
        
        return {
            'success': False, 
            'error': 'All download methods failed. YouTube may be blocking downloads from your region or IP address. Try using a VPN or try again later.'
        }
    
    @staticmethod
    def _try_download_method_1(url, media_type, download_dir, quality):
        """Method 1: Standard download with quality support"""
        try:
            ydl_opts = VideoDownloader.get_ydl_opts(media_type, download_dir, quality)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                logger.info(f"Method 1 - Extracting: {info.get('title', 'Unknown')} with quality: {quality}")
                ydl.download([url])
                
                filename = VideoDownloader._get_final_filename(ydl, info, media_type, download_dir)
                return {
                    'filename': os.path.basename(filename),
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'success': True
                }
        except Exception as e:
            logger.warning(f"Method 1 failed: {e}")
            return {'success': False}
    
    @staticmethod
    def _try_download_method_2(url, media_type, download_dir, quality):
        """Method 2: Alternative format selection with quality"""
        try:
            if media_type == 'mp4':
                # Map quality to height constraints
                quality_map = {
                    'best': '[height<=1080]',
                    '1080p': '[height<=1080]',
                    '720p': '[height<=720]',
                    '480p': '[height<=480]',
                    '360p': '[height<=360]'
                }
                quality_suffix = quality_map.get(quality, '')
                format_spec = f'best{quality_suffix}/best[height<=480]/best[height<=360]/best'
            else:
                # Audio quality
                quality_map = {
                    'best': '320',
                    '192k': '192',
                    '128k': '128',
                    '64k': '64'
                }
                audio_quality = quality_map.get(quality, '192')
                format_spec = 'bestaudio/best'
            
            ydl_opts = {
                'format': format_spec,
                'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
                'quiet': False,
                'no_warnings': False,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Referer': 'https://www.youtube.com/',
                    'Origin': 'https://www.youtube.com',
                },
                'retries': 5,
                'fragment_retries': 5,
            }
            
            if media_type == 'mp3':
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }]
            elif media_type == 'mp4':
                ydl_opts['merge_output_format'] = 'mp4'
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                logger.info(f"Method 2 - Extracting: {info.get('title', 'Unknown')} with quality: {quality}")
                ydl.download([url])
                
                filename = VideoDownloader._get_final_filename(ydl, info, media_type, download_dir)
                return {
                    'filename': os.path.basename(filename),
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'success': True
                }
        except Exception as e:
            logger.warning(f"Method 2 failed: {e}")
            return {'success': False}
    
    @staticmethod
    def _try_download_method_3(url, media_type, download_dir, quality):
        """Method 3: Simple format for maximum compatibility with quality"""
        try:
            # Simplest possible format selection with quality consideration
            if media_type == 'mp4':
                format_spec = 'mp4/best'
            else:
                format_spec = 'm4a/bestaudio/best'
            
            ydl_opts = {
                'format': format_spec,
                'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
                'quiet': False,
                'no_warnings': False,
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
                    'Accept': '*/*',
                },
            }
            
            if media_type == 'mp3':
                # Simple audio quality setting
                quality_map = {
                    'best': '320',
                    '192k': '192',
                    '128k': '128',
                    '64k': '64'
                }
                audio_quality = quality_map.get(quality, '192')
                
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': audio_quality,
                }]
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                logger.info(f"Method 3 - Extracting: {info.get('title', 'Unknown')} with quality: {quality}")
                ydl.download([url])
                
                filename = VideoDownloader._get_final_filename(ydl, info, media_type, download_dir)
                return {
                    'filename': os.path.basename(filename),
                    'title': info.get('title', 'Unknown'),
                    'thumbnail': info.get('thumbnail', ''),
                    'success': True
                }
        except Exception as e:
            logger.warning(f"Method 3 failed: {e}")
            return {'success': False}
    
    @staticmethod
    def _get_final_filename(ydl, info, media_type, download_dir):
        """Get the final filename after download"""
        filename = ydl.prepare_filename(info)
        
        if media_type == 'mp3':
            # For MP3, look for the converted file
            base_name = os.path.splitext(filename)[0]
            expected_mp3 = base_name + '.mp3'
            if os.path.exists(expected_mp3):
                return expected_mp3
            # Fallback to original filename if conversion didn't happen
            return filename
        elif media_type == 'mp4':
            # Ensure MP4 extension
            base, ext = os.path.splitext(filename)
            if ext.lower() != '.mp4':
                expected_mp4 = base + '.mp4'
                # Check if file was merged to MP4
                if os.path.exists(expected_mp4):
                    return expected_mp4
            return filename
        return filename
    
    @staticmethod
    def _download_instagram(url, media_type, quality='best'):
        """Download from Instagram with quality support"""
        download_dir = 'downloads'
        os.makedirs(download_dir, exist_ok=True)
        
        # Instagram typically has limited quality options, but we'll handle it
        if media_type == 'mp4':
            format_spec = 'best'  # Instagram usually has one video quality
        else:
            format_spec = 'bestaudio/best'
        
        ydl_opts = {
            'format': format_spec,
            'outtmpl': f'{download_dir}/%(title)s.%(ext)s',
            'quiet': False,
            'no_warnings': False,
        }
        
        if media_type == 'mp3':
            # Audio quality for Instagram
            quality_map = {
                'best': '192',
                '192k': '192',
                '128k': '128',
                '64k': '64'
            }
            audio_quality = quality_map.get(quality, '192')
            
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': audio_quality,
            }]
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                ydl.download([url])
                
                filename = ydl.prepare_filename(info)
                if media_type == 'mp3':
                    filename = filename.rsplit('.', 1)[0] + '.mp3'
                
                return {
                    'filename': os.path.basename(filename),
                    'title': info.get('title', 'Instagram Media'),
                    'thumbnail': info.get('thumbnail', ''),
                    'success': True
                }
        except Exception as e:
            logger.error(f"Instagram download error: {e}")
            return {'success': False, 'error': str(e)}
    
    @staticmethod
    def get_quality_options(media_type, platform):
        """Get available quality options for the specified media type and platform"""
        if media_type == 'mp3':
            return [
                {'value': 'best', 'label': 'Best Quality (320kbps)'},
                {'value': '192k', 'label': 'High Quality (192kbps)'},
                {'value': '128k', 'label': 'Good Quality (128kbps)'},
                {'value': '64k', 'label': 'Standard Quality (64kbps)'}
            ]
        else:  # mp4
            if platform == 'youtube':
                return [
                    {'value': 'best', 'label': 'Best Available (up to 1080p)'},
                    {'value': '1080p', 'label': 'Full HD (1080p)'},
                    {'value': '720p', 'label': 'HD (720p)'},
                    {'value': '480p', 'label': 'Standard (480p)'},
                    {'value': '360p', 'label': 'Low (360p)'}
                ]
            else:  # Instagram
                return [
                    {'value': 'best', 'label': 'Best Available'},
                    {'value': '720p', 'label': 'HD (720p)'},
                    {'value': '480p', 'label': 'Standard (480p)'}
                ]