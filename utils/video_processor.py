import os
import json
import logging
from urllib.parse import urlparse, parse_qs
import requests
from datetime import datetime
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoProcessor:
    """Handles video processing, validation, and metadata extraction"""
    
    @staticmethod
    def validate_url(url, platform):
        """
        Validate if the URL is appropriate for the selected platform
        
        Args:
            url (str): The video URL to validate
            platform (str): 'youtube' or 'instagram'
            
        Returns:
            dict: Validation result with success status and message
        """
        try:
            parsed_url = urlparse(url)
            
            if not parsed_url.scheme in ['http', 'https']:
                return {'success': False, 'error': 'Invalid URL scheme. URL must start with http:// or https://'}
            
            if platform == 'youtube':
                return VideoProcessor._validate_youtube_url(url)
            elif platform == 'instagram':
                return VideoProcessor._validate_instagram_url(url)
            else:
                return {'success': False, 'error': 'Unsupported platform'}
                
        except Exception as e:
            logger.error(f"URL validation error: {e}")
            return {'success': False, 'error': 'Invalid URL format'}
    
    @staticmethod
    def _validate_youtube_url(url):
        """Validate YouTube URL patterns"""
        # More comprehensive YouTube URL patterns
        youtube_patterns = [
            # Standard YouTube watch URLs
            r'^(https?://)?(www\.)?youtube\.com/watch\?v=[a-zA-Z0-9_-]{11}',
            # YouTube with additional parameters
            r'^(https?://)?(www\.)?youtube\.com/watch\?.+&v=[a-zA-Z0-9_-]{11}',
            # Short youtu.be URLs
            r'^(https?://)?(www\.)?youtu\.be/[a-zA-Z0-9_-]{11}',
            # Embed URLs
            r'^(https?://)?(www\.)?youtube\.com/embed/[a-zA-Z0-9_-]{11}',
            # Mobile URLs
            r'^(https?://)?m\.youtube\.com/watch\?v=[a-zA-Z0-9_-]{11}',
            # YouTube Shorts
            r'^(https?://)?(www\.)?youtube\.com/shorts/[a-zA-Z0-9_-]{11}',
            # YouTube live streams
            r'^(https?://)?(www\.)?youtube\.com/live/[a-zA-Z0-9_-]{11}',
        ]
        
        for pattern in youtube_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                video_id = VideoProcessor._extract_youtube_id(url)
                if video_id and len(video_id) == 11:
                    return {
                        'success': True, 
                        'video_id': video_id,
                        'message': 'Valid YouTube URL'
                    }
        
        return {'success': False, 'error': 'Invalid YouTube URL. Please use a standard YouTube video URL.'}
    
    @staticmethod
    def _validate_instagram_url(url):
        """Validate Instagram URL patterns"""
        instagram_patterns = [
            r'^(https?://)?(www\.)?instagram\.com/p/[a-zA-Z0-9_-]+',
            r'^(https?://)?(www\.)?instagram\.com/reel/[a-zA-Z0-9_-]+',
            r'^(https?://)?(www\.)?instagram\.com/tv/[a-zA-Z0-9_-]+',
            r'^(https?://)?(www\.)?instagram\.com/stories/[a-zA-Z0-9_-]+',
            # Instagram with query parameters
            r'^(https?://)?(www\.)?instagram\.com/p/[a-zA-Z0-9_-]+/?\?',
            r'^(https?://)?(www\.)?instagram\.com/reel/[a-zA-Z0-9_-]+/?\?',
        ]
        
        for pattern in instagram_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return {
                    'success': True,
                    'message': 'Valid Instagram URL'
                }
        
        return {'success': False, 'error': 'Invalid Instagram URL. Please use a standard Instagram post, reel, or story URL.'}
    
    @staticmethod
    def _extract_youtube_id(url):
        """Extract YouTube video ID from URL using multiple methods"""
        try:
            # Method 1: Standard v= parameter
            standard_match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
            if standard_match:
                return standard_match.group(1)
            
            # Method 2: youtu.be short URLs
            short_match = re.search(r'youtu\.be\/([0-9A-Za-z_-]{11})', url)
            if short_match:
                return short_match.group(1)
            
            # Method 3: Embed URLs
            embed_match = re.search(r'embed\/([0-9A-Za-z_-]{11})', url)
            if embed_match:
                return embed_match.group(1)
            
            # Method 4: YouTube Shorts
            shorts_match = re.search(r'shorts\/([0-9A-Za-z_-]{11})', url)
            if shorts_match:
                return shorts_match.group(1)
            
            # Method 5: Live streams
            live_match = re.search(r'live\/([0-9A-Za-z_-]{11})', url)
            if live_match:
                return live_match.group(1)
            
            # Method 6: Parse query parameters
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            if 'v' in query_params:
                video_id = query_params['v'][0]
                if len(video_id) == 11:
                    return video_id
                    
        except Exception as e:
            logger.error(f"Error extracting YouTube ID: {e}")
            
        return None
    
    @staticmethod
    def extract_metadata(url, platform):
        """
        Extract additional metadata from video URL
        
        Args:
            url (str): Video URL
            platform (str): Platform name
            
        Returns:
            dict: Metadata information
        """
        try:
            if platform == 'youtube':
                return VideoProcessor._extract_youtube_metadata(url)
            elif platform == 'instagram':
                return VideoProcessor._extract_instagram_metadata(url)
            else:
                return {}
        except Exception as e:
            logger.error(f"Metadata extraction error: {e}")
            return {}
    
    @staticmethod
    def _extract_youtube_metadata(url):
        """Extract YouTube-specific metadata"""
        metadata = {}
        video_id = VideoProcessor._extract_youtube_id(url)
        
        if video_id:
            metadata.update({
                'video_id': video_id,
                'embed_url': f'https://www.youtube.com/embed/{video_id}',
                'thumbnail_url': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
                'thumbnail_url_sd': f'https://img.youtube.com/vi/{video_id}/sddefault.jpg',
                'thumbnail_url_mq': f'https://img.youtube.com/vi/{video_id}/mqdefault.jpg',
                'thumbnail_url_hq': f'https://img.youtube.com/vi/{video_id}/hqdefault.jpg',
                'webpage_url': f'https://www.youtube.com/watch?v={video_id}'
            })
        
        # Extract timestamp from URL if present
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        
        if 't' in query_params:
            metadata['start_time'] = query_params['t'][0]
        elif 'start' in query_params:
            metadata['start_time'] = query_params['start'][0]
        
        # Extract other parameters
        if 'list' in query_params:
            metadata['playlist_id'] = query_params['list'][0]
            
        return metadata
    
    @staticmethod
    def _extract_instagram_metadata(url):
        """Extract Instagram-specific metadata"""
        metadata = {}
        
        try:
            # Extract post ID from URL
            patterns = [
                r'/p/([a-zA-Z0-9_-]+)',
                r'/reel/([a-zA-Z0-9_-]+)',
                r'/tv/([a-zA-Z0-9_-]+)',
                r'/stories/([a-zA-Z0-9_-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    metadata['post_id'] = match.group(1)
                    break
                    
            # Extract username from stories
            stories_match = re.search(r'/stories/([a-zA-Z0-9_.]+)/([0-9]+)', url)
            if stories_match:
                metadata['username'] = stories_match.group(1)
                metadata['story_id'] = stories_match.group(2)
                
        except Exception as e:
            logger.error(f"Error extracting Instagram metadata: {e}")
            
        return metadata
    
    @staticmethod
    def get_available_formats(url, platform):
        """
        Get available formats for the video
        
        Args:
            url (str): Video URL
            platform (str): Platform name
            
        Returns:
            dict: Available formats information
        """
        try:
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = {
                    'video_formats': [],
                    'audio_formats': [],
                    'best_video': None,
                    'best_audio': None,
                    'duration': info.get('duration', 0),
                    'file_sizes': {}
                }
                
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
                            formats['video_formats'].append(format_info)
                        elif fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                            formats['audio_formats'].append(format_info)
                
                # Find best quality formats
                if formats['video_formats']:
                    formats['best_video'] = max(
                        formats['video_formats'], 
                        key=lambda x: x.get('filesize', 0) or 0
                    )
                
                if formats['audio_formats']:
                    formats['best_audio'] = max(
                        formats['audio_formats'],
                        key=lambda x: x.get('filesize', 0) or 0
                    )
                
                # Calculate approximate file sizes
                if formats['best_video']:
                    formats['file_sizes']['video'] = VideoProcessor._bytes_to_human_readable(
                        formats['best_video'].get('filesize', 0) or 0
                    )
                
                if formats['best_audio']:
                    formats['file_sizes']['audio'] = VideoProcessor._bytes_to_human_readable(
                        formats['best_audio'].get('filesize', 0) or 0
                    )
                
                return formats
                
        except Exception as e:
            logger.error(f"Format extraction error: {e}")
            return {
                'video_formats': [],
                'audio_formats': [],
                'best_video': None,
                'best_audio': None,
                'duration': 0,
                'file_sizes': {}
            }
    
    @staticmethod
    def get_quality_options(media_type, platform, available_formats=None):
        """
        Get available quality options based on media type and platform
        
        Args:
            media_type (str): 'mp4' or 'mp3'
            platform (str): 'youtube' or 'instagram'
            available_formats (dict): Available formats from get_available_formats
            
        Returns:
            list: List of quality options with value and label
        """
        if media_type == 'mp3':
            # Audio quality options
            return [
                {'value': 'best', 'label': 'Best Quality (320kbps)'},
                {'value': '192k', 'label': 'High Quality (192kbps)'},
                {'value': '128k', 'label': 'Good Quality (128kbps)'},
                {'value': '64k', 'label': 'Standard Quality (64kbps)'}
            ]
        else:
            # Video quality options
            if platform == 'youtube':
                qualities = [
                    {'value': 'best', 'label': 'Best Available (up to 1080p)'},
                    {'value': '1080p', 'label': 'Full HD (1080p)'},
                    {'value': '720p', 'label': 'HD (720p)'},
                    {'value': '480p', 'label': 'Standard (480p)'},
                    {'value': '360p', 'label': 'Low (360p)'}
                ]
                
                # Filter based on available formats if provided
                if available_formats and available_formats.get('video_formats'):
                    available_heights = set()
                    for fmt in available_formats['video_formats']:
                        if fmt.get('height'):
                            available_heights.add(fmt['height'])
                    
                    # Filter qualities based on available heights
                    filtered_qualities = []
                    for quality in qualities:
                        if quality['value'] == 'best':
                            filtered_qualities.append(quality)
                        else:
                            # Extract height from quality value (e.g., '1080p' -> 1080)
                            height = int(quality['value'].replace('p', ''))
                            if any(h >= height for h in available_heights):
                                filtered_qualities.append(quality)
                    
                    return filtered_qualities if filtered_qualities else qualities
                
                return qualities
            else:  # Instagram
                return [
                    {'value': 'best', 'label': 'Best Available'},
                    {'value': '720p', 'label': 'HD (720p)'},
                    {'value': '480p', 'label': 'Standard (480p)'}
                ]
    
    @staticmethod
    def sanitize_filename(filename):
        """
        Sanitize filename to remove invalid characters
        
        Args:
            filename (str): Original filename
            
        Returns:
            str: Sanitized filename
        """
        if not filename:
            return "download"
            
        # Remove invalid characters for filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Replace multiple spaces with single space
        filename = re.sub(r'\s+', ' ', filename)
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Limit filename length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        
        # Ensure filename is not empty
        if not filename:
            filename = "video_download"
            
        return filename
    
    @staticmethod
    def get_file_size(filepath):
        """
        Get human-readable file size
        
        Args:
            filepath (str): Path to the file
            
        Returns:
            str: Human-readable file size
        """
        try:
            if os.path.exists(filepath):
                size_bytes = os.path.getsize(filepath)
                return VideoProcessor._bytes_to_human_readable(size_bytes)
            else:
                return "File not found"
        except OSError as e:
            logger.error(f"Error getting file size: {e}")
            return "Unknown"
    
    @staticmethod
    def _bytes_to_human_readable(size_bytes):
        """Convert bytes to human-readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
        
        return f"{size:.2f} {size_names[i]}"
    
    @staticmethod
    def cleanup_old_files(directory='downloads', max_age_hours=24):
        """
        Clean up old downloaded files
        
        Args:
            directory (str): Directory to clean up
            max_age_hours (int): Maximum age of files in hours
        """
        try:
            if not os.path.exists(directory):
                logger.info(f"Download directory {directory} does not exist")
                return
            
            current_time = datetime.now()
            max_age_seconds = max_age_hours * 3600
            cleaned_count = 0
            
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                
                if os.path.isfile(filepath):
                    try:
                        file_time = datetime.fromtimestamp(os.path.getctime(filepath))
                        file_age = (current_time - file_time).total_seconds()
                        
                        if file_age > max_age_seconds:
                            os.remove(filepath)
                            cleaned_count += 1
                            logger.info(f"Cleaned up old file: {filename}")
                    except OSError as e:
                        logger.error(f"Error cleaning up file {filename}: {e}")
            
            logger.info(f"Cleanup completed. Removed {cleaned_count} files.")
                        
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    @staticmethod
    def get_download_stats(directory='downloads'):
        """
        Get download directory statistics
        
        Args:
            directory (str): Download directory path
            
        Returns:
            dict: Directory statistics
        """
        try:
            if not os.path.exists(directory):
                return {
                    'total_files': 0,
                    'total_size': '0 B',
                    'total_size_bytes': 0,
                    'directory_exists': False
                }
            
            total_size = 0
            file_count = 0
            file_types = {}
            
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_size = os.path.getsize(filepath)
                    total_size += file_size
                    file_count += 1
                    
                    # Count file types
                    file_ext = os.path.splitext(filename)[1].lower()
                    file_types[file_ext] = file_types.get(file_ext, 0) + 1
            
            return {
                'total_files': file_count,
                'total_size': VideoProcessor._bytes_to_human_readable(total_size),
                'total_size_bytes': total_size,
                'file_types': file_types,
                'directory_exists': True
            }
            
        except Exception as e:
            logger.error(f"Stats calculation error: {e}")
            return {
                'total_files': 0,
                'total_size': '0 B',
                'total_size_bytes': 0,
                'file_types': {},
                'directory_exists': False
            }
    
    @staticmethod
    def generate_download_report(user_downloads):
        """
        Generate a download report for a user
        
        Args:
            user_downloads (list): List of Download objects
            
        Returns:
            dict: Download statistics report
        """
        try:
            total_downloads = len(user_downloads)
            
            if total_downloads == 0:
                return {
                    'total_downloads': 0,
                    'platform_distribution': {},
                    'media_type_distribution': {},
                    'recent_downloads_7_days': 0,
                    'most_used_platform': 'None',
                    'most_used_media_type': 'None',
                    'first_download': None,
                    'last_download': None
                }
            
            # Count by platform and media type
            platform_counts = {}
            media_type_counts = {}
            download_dates = []
            
            for download in user_downloads:
                platform = download.platform
                media_type = download.media_type
                
                platform_counts[platform] = platform_counts.get(platform, 0) + 1
                media_type_counts[media_type] = media_type_counts.get(media_type, 0) + 1
                download_dates.append(download.downloaded_at)
            
            # Recent downloads (last 7 days)
            week_ago = datetime.now().timestamp() - (7 * 24 * 3600)
            recent_downloads = [
                download for download in user_downloads 
                if download.downloaded_at.timestamp() > week_ago
            ]
            
            # Date range
            download_dates.sort()
            first_download = download_dates[0] if download_dates else None
            last_download = download_dates[-1] if download_dates else None
            
            return {
                'total_downloads': total_downloads,
                'platform_distribution': platform_counts,
                'media_type_distribution': media_type_counts,
                'recent_downloads_7_days': len(recent_downloads),
                'most_used_platform': max(platform_counts, key=platform_counts.get) if platform_counts else 'None',
                'most_used_media_type': max(media_type_counts, key=media_type_counts.get) if media_type_counts else 'None',
                'first_download': first_download.isoformat() if first_download else None,
                'last_download': last_download.isoformat() if last_download else None
            }
            
        except Exception as e:
            logger.error(f"Report generation error: {e}")
            return {
                'total_downloads': 0,
                'platform_distribution': {},
                'media_type_distribution': {},
                'recent_downloads_7_days': 0,
                'most_used_platform': 'None',
                'most_used_media_type': 'None',
                'first_download': None,
                'last_download': None
            }
    
    @staticmethod
    def validate_download_path(filename, download_dir='downloads'):
        """
        Validate and secure download path to prevent directory traversal
        
        Args:
            filename (str): Requested filename
            download_dir (str): Download directory
            
        Returns:
            tuple: (safe_filepath, error_message)
        """
        try:
            if not filename or not isinstance(filename, str):
                return None, "Invalid filename"
            
            # Normalize path and get basename only
            safe_filename = os.path.basename(filename)
            if safe_filename != filename:
                return None, "Invalid filename path"
            
            # Ensure download directory exists
            os.makedirs(download_dir, exist_ok=True)
            
            safe_filepath = os.path.join(download_dir, safe_filename)
            
            # Ensure the path stays within download directory
            if not os.path.realpath(safe_filepath).startswith(os.path.realpath(download_dir)):
                return None, "Invalid file path - directory traversal detected"
            
            return safe_filepath, None
            
        except Exception as e:
            logger.error(f"Path validation error: {e}")
            return None, "Path validation failed"
    
    @staticmethod
    def get_video_duration_formatted(seconds):
        """
        Convert seconds to formatted duration string
        
        Args:
            seconds (int): Duration in seconds
            
        Returns:
            str: Formatted duration (HH:MM:SS or MM:SS)
        """
        if not seconds:
            return "Unknown"
        
        try:
            seconds = int(seconds)
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            seconds = seconds % 60
            
            if hours > 0:
                return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes:02d}:{seconds:02d}"
        except (ValueError, TypeError):
            return "Unknown"
    
    @staticmethod
    def estimate_download_time(file_size_mb, download_speed_mbps=5):
        """
        Estimate download time based on file size
        
        Args:
            file_size_mb (float): File size in MB
            download_speed_mbps (float): Download speed in Mbps
            
        Returns:
            str: Estimated download time
        """
        if not file_size_mb or file_size_mb <= 0:
            return "Unknown"
        
        try:
            # Convert MB to Mb (1 MB = 8 Mb)
            file_size_mb = float(file_size_mb) * 8
            
            # Calculate time in seconds
            time_seconds = file_size_mb / download_speed_mbps
            
            if time_seconds < 60:
                return f"{int(time_seconds)} seconds"
            elif time_seconds < 3600:
                minutes = int(time_seconds // 60)
                seconds = int(time_seconds % 60)
                return f"{minutes}m {seconds}s"
            else:
                hours = int(time_seconds // 3600)
                minutes = int((time_seconds % 3600) // 60)
                return f"{hours}h {minutes}m"
                
        except (ValueError, TypeError, ZeroDivisionError):
            return "Unknown"
    
    @staticmethod
    def test_youtube_url(url):
        """Test method to debug YouTube URL validation"""
        print(f"Testing URL: {url}")
        
        # Test extraction
        video_id = VideoProcessor._extract_youtube_id(url)
        print(f"Extracted Video ID: {video_id}")
        
        # Test validation
        validation = VideoProcessor._validate_youtube_url(url)
        print(f"Validation Result: {validation}")
        
        return video_id, validation
    
    @staticmethod
    def get_platform_from_url(url):
        """
        Automatically detect platform from URL
        
        Args:
            url (str): Video URL
            
        Returns:
            str: Detected platform ('youtube', 'instagram', or 'unknown')
        """
        if not url:
            return 'unknown'
            
        url_lower = url.lower()
        
        if any(domain in url_lower for domain in ['youtube.com', 'youtu.be']):
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        else:
            return 'unknown'
    
    @staticmethod
    def format_quality_label(format_info):
        """
        Create a user-friendly quality label from format info
        
        Args:
            format_info (dict): Format information
            
        Returns:
            str: User-friendly quality label
        """
        try:
            quality_parts = []
            
            if format_info.get('height'):
                quality_parts.append(f"{format_info['height']}p")
            
            if format_info.get('fps'):
                quality_parts.append(f"{format_info['fps']}fps")
            
            if format_info.get('quality') and format_info['quality'] != 'unknown':
                quality_parts.append(format_info['quality'])
            
            if format_info.get('ext') and format_info['ext'] != 'unknown':
                quality_parts.append(format_info['ext'].upper())
            
            return ' • '.join(quality_parts) if quality_parts else 'Unknown quality'
            
        except Exception as e:
            logger.error(f"Error formatting quality label: {e}")
            return 'Unknown quality'
    
    @staticmethod
    def is_video_age_restricted(video_info):
        """
        Check if video is age-restricted
        
        Args:
            video_info (dict): Video information from yt-dlp
            
        Returns:
            bool: True if age-restricted
        """
        try:
            # Check various indicators of age restriction
            age_indicators = [
                video_info.get('age_limit', 0) > 0,
                'age restriction' in str(video_info).lower(),
                'sign in to confirm' in str(video_info).lower(),
                'content warning' in str(video_info).lower()
            ]
            
            return any(age_indicators)
            
        except Exception as e:
            logger.error(f"Error checking age restriction: {e}")
            return False
    
    @staticmethod
    def get_supported_platforms():
        """
        Get list of supported platforms and their capabilities
        
        Returns:
            dict: Supported platforms information
        """
        return {
            'youtube': {
                'name': 'YouTube',
                'supports_video': True,
                'supports_audio': True,
                'max_resolution': '4K',
                'formats': ['MP4', 'MP3', 'WEBM'],
                'icon': 'fab fa-youtube'
            },
            'instagram': {
                'name': 'Instagram',
                'supports_video': True,
                'supports_audio': True,
                'max_resolution': '1080p',
                'formats': ['MP4', 'MP3'],
                'icon': 'fab fa-instagram'
            }
        }
