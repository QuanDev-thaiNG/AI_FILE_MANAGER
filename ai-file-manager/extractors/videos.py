import subprocess
import json
import os
from pathlib import Path

class VideoExtractor:
    """Lớp trích xuất metadata từ file video sử dụng ffprobe"""
    
    def __init__(self, ffprobe_path='ffprobe'):
        """Khởi tạo với đường dẫn đến ffprobe"""
        self.ffprobe_path = ffprobe_path
    
    def extract_metadata(self, file_path):
        """Trích xuất metadata từ file video"""
        metadata = {}
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        try:
            # Sử dụng ffprobe để lấy thông tin
            cmd = [
                self.ffprobe_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                str(file_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"Lỗi khi chạy ffprobe: {result.stderr}")
                return metadata
            
            # Parse JSON output
            probe_data = json.loads(result.stdout)
            
            # Lấy thông tin format
            if 'format' in probe_data:
                format_data = probe_data['format']
                
                # Thời lượng
                if 'duration' in format_data:
                    metadata['duration'] = float(format_data['duration'])
                
                # Bitrate
                if 'bit_rate' in format_data:
                    metadata['bitrate'] = int(format_data['bit_rate'])
                
                # Kích thước file
                if 'size' in format_data:
                    metadata['size'] = int(format_data['size'])
                
                # Định dạng
                if 'format_name' in format_data:
                    metadata['format'] = format_data['format_name']
                
                # Tên
                if 'tags' in format_data and 'title' in format_data['tags']:
                    metadata['title'] = format_data['tags']['title']
            
            # Lấy thông tin stream
            if 'streams' in probe_data:
                video_stream = None
                audio_stream = None
                
                # Tìm stream video và audio đầu tiên
                for stream in probe_data['streams']:
                    if stream['codec_type'] == 'video' and not video_stream:
                        video_stream = stream
                    elif stream['codec_type'] == 'audio' and not audio_stream:
                        audio_stream = stream
                
                # Xử lý stream video
                if video_stream:
                    # Codec
                    if 'codec_name' in video_stream:
                        metadata['codec'] = video_stream['codec_name']
                    
                    # Độ phân giải
                    if 'width' in video_stream and 'height' in video_stream:
                        metadata['width'] = video_stream['width']
                        metadata['height'] = video_stream['height']
                        metadata['resolution'] = f"{video_stream['width']}x{video_stream['height']}"
                    
                    # FPS
                    if 'r_frame_rate' in video_stream:
                        fps_parts = video_stream['r_frame_rate'].split('/')
                        if len(fps_parts) == 2 and int(fps_parts[1]) != 0:
                            metadata['fps'] = float(int(fps_parts[0]) / int(fps_parts[1]))
                
                # Xử lý stream audio
                if audio_stream:
                    # Audio codec
                    if 'codec_name' in audio_stream:
                        metadata['audio_codec'] = audio_stream['codec_name']
                    
                    # Sample rate
                    if 'sample_rate' in audio_stream:
                        metadata['samplerate'] = int(audio_stream['sample_rate'])
                    
                    # Channels
                    if 'channels' in audio_stream:
                        metadata['audio_channels'] = audio_stream['channels']
        except Exception as e:
            print(f"Lỗi khi trích xuất metadata từ video: {e}")
        
        return metadata
    
    def extract_frames(self, file_path, output_dir, interval=60, max_frames=10):
        """Trích xuất các khung hình từ video theo khoảng thời gian"""
        path = Path(file_path)
        output_path = Path(output_dir)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        output_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Lấy thời lượng video
            metadata = self.extract_metadata(file_path)
            duration = metadata.get('duration', 0)
            
            if duration <= 0:
                print(f"Không thể xác định thời lượng của video: {file_path}")
                return []
            
            # Tính toán các thời điểm trích xuất khung hình
            timestamps = []
            for i in range(min(max_frames, int(duration // interval) + 1)):
                timestamps.append(i * interval)
            
            # Trích xuất khung hình tại mỗi thời điểm
            frame_paths = []
            for i, timestamp in enumerate(timestamps):
                output_file = output_path / f"frame_{i:03d}_{timestamp}s.jpg"
                frame_paths.append(str(output_file))
                
                cmd = [
                    'ffmpeg',
                    '-ss', str(timestamp),
                    '-i', str(file_path),
                    '-vframes', '1',
                    '-q:v', '2',
                    str(output_file),
                    '-y'
                ]
                
                subprocess.run(cmd, capture_output=True)
            
            return frame_paths
        except Exception as e:
            print(f"Lỗi khi trích xuất khung hình từ video: {e}")
            return []
    
    def extract_audio(self, file_path, output_file=None):
        """Trích xuất audio từ video"""
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"File không tồn tại: {file_path}")
        
        if not output_file:
            output_file = str(path.with_suffix('.mp3'))
        
        try:
            cmd = [
                'ffmpeg',
                '-i', str(file_path),
                '-q:a', '0',
                '-map', 'a',
                str(output_file),
                '-y'
            ]
            
            subprocess.run(cmd, capture_output=True)
            return output_file
        except Exception as e:
            print(f"Lỗi khi trích xuất audio từ video: {e}")
            return None