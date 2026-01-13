"""
Audio Buffer - Per-user audio recording
"""

import wave
from pathlib import Path
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AudioBuffer:
    """Buffer for capturing and writing per-user audio"""
    
    def __init__(self, user_id, username, session_id, output_dir):
        self.user_id = user_id
        self.username = username
        self.session_id = session_id
        
        # Create output path with readable filename
        session_dir = Path(output_dir) / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        # Create filename: Username_2026-01-12_01-30-45.wav
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        # Clean username (remove special characters that can't be in filenames)
        clean_username = ''.join(c for c in username if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_username = clean_username.replace(' ', '_')
        
        self.output_path = session_dir / f'{clean_username}_{timestamp}.wav'
        
        # Discord audio specs
        self.sample_rate = 48000
        self.channels = 2
        self.sample_width = 2
        
        self.wav_file = None
        self.frames_written = 0
        
        logger.info(f'Audio buffer created for {username} -> {self.output_path}')
    
    def open(self):
        """Open WAV file for writing"""
        self.wav_file = wave.open(str(self.output_path), 'wb')
        self.wav_file.setnchannels(self.channels)
        self.wav_file.setsampwidth(self.sample_width)
        self.wav_file.setframerate(self.sample_rate)
        logger.info(f'Opened WAV file: {self.output_path}')
    
    def write(self, pcm_data):
        """Write PCM audio data"""
        if not self.wav_file:
            self.open()
        
        self.wav_file.writeframes(pcm_data)
        self.frames_written += len(pcm_data) // (self.sample_width * self.channels)
    
    def close(self):
        """Close and finalize WAV file"""
        if self.wav_file:
            self.wav_file.close()
            self.wav_file = None
            logger.info(f'Closed WAV file: {self.output_path} ({self.duration:.1f}s)')
    
    @property
    def duration(self):
        """Get duration in seconds"""
        return self.frames_written / self.sample_rate
    
    @property
    def size(self):
        """Get file size in bytes"""
        if self.output_path.exists():
            return self.output_path.stat().st_size
        return 0
