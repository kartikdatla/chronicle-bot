"""
Per-User Audio Sink with Timestamp Tracking

Captures per-user audio streams with timestamps for chronological ordering
"""

import discord
import wave
import logging
from pathlib import Path
from datetime import datetime
import json
import time

logger = logging.getLogger(__name__)


class PerUserWavSink(discord.sinks.Sink):
    """
    Pycord sink that saves per-user audio with timestamp tracking
    """
    
    def __init__(self, output_dir, session_id, participants):
        super().__init__()
        
        self.output_dir = Path(output_dir) / session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = session_id
        self.participants = {p.id: p for p in participants}
        self.session_start_time = time.time()
        
        # Track timestamps for each audio chunk
        self.audio_timestamps = {}  # {user_id: [(timestamp, data_length), ...]}
        
        # Prevent duplicate cleanup calls
        self._cleanup_called = False
        
        logger.info(
            f'PerUserWavSink initialized: session={session_id[:8]}, '
            f'participants={len(participants)}, path={self.output_dir}'
        )
    
    def write(self, data, user):
        """
        Override write to track timestamps
        Called by Pycord whenever audio data is received
        """
        # Call parent to store audio data
        super().write(data, user)
        
        # Track timestamp for this chunk
        user_id = user if isinstance(user, int) else user.id
        
        if user_id not in self.audio_timestamps:
            self.audio_timestamps[user_id] = []
        
        # Record timestamp relative to session start and data length
        timestamp = time.time() - self.session_start_time
        data_length = len(data) if hasattr(data, '__len__') else 0
        
        self.audio_timestamps[user_id].append((timestamp, data_length))
    
    def cleanup(self):
        """
        Save all recorded audio to individual WAV files with timestamp metadata
        """
        # Prevent duplicate saves
        if self._cleanup_called:
            logger.warning('⚠️ Cleanup already called, skipping duplicate save')
            return {}
        
        self._cleanup_called = True
        
        logger.info(f'🎵 Saving audio for {len(self.audio_data)} users')
        
        if not self.audio_data:
            logger.warning('No audio data to save')
            return {}
        
        saved_files = {}
        timestamp_metadata = {}
        errors = []
        
        for user_id, audio_data in self.audio_data.items():
            try:
                result = self._save_user_audio(user_id, audio_data)
                if result:
                    saved_files[user_id] = result
                    
                    # Save timestamp metadata
                    if user_id in self.audio_timestamps:
                        timestamp_metadata[user_id] = {
                            'username': result['username'],
                            'timestamps': self.audio_timestamps[user_id]
                        }
                        
            except Exception as e:
                error_msg = f'Failed to save audio for user {user_id}: {e}'
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        # Save timestamp metadata to JSON file
        if timestamp_metadata:
            metadata_path = self.output_dir / 'timestamps.json'
            try:
                with open(metadata_path, 'w') as f:
                    json.dump(timestamp_metadata, f, indent=2)
                logger.info(f'✅ Saved timestamp metadata: {metadata_path}')
            except Exception as e:
                logger.error(f'Failed to save timestamp metadata: {e}')
        
        if saved_files:
            logger.info(f'✅ Successfully saved {len(saved_files)} audio files')
        
        if errors:
            logger.warning(f'⚠️ {len(errors)} files failed to save')
        
        return saved_files
    
    def _save_user_audio(self, user_id, audio_data):
        """Save audio for a single user"""
        user = self.participants.get(user_id)
        if not user:
            logger.warning(f'No user info for ID {user_id}, using fallback name')
            username = f'user_{user_id}'
        else:
            username = user.name
        
        # Read PCM audio data
        audio_data.file.seek(0)
        pcm_data = audio_data.file.read()
        
        # Validate audio data
        if len(pcm_data) == 0:
            logger.warning(f'No audio data for {username} (user did not speak)')
            return None
        
        if len(pcm_data) < 1000:
            logger.warning(f'Audio too short for {username}, skipping')
            return None
        
        # Create safe filename with timestamp
        clean_name = self._sanitize_filename(username)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{clean_name}_{timestamp}.wav'
        file_path = self.output_dir / filename
        
        # Check if file already exists (shouldn't happen, but prevent overwrites)
        if file_path.exists():
            logger.warning(f'File {filename} already exists, adding suffix')
            counter = 1
            while file_path.exists():
                filename = f'{clean_name}_{timestamp}_{counter}.wav'
                file_path = self.output_dir / filename
                counter += 1
        
        # Write WAV file
        try:
            with wave.open(str(file_path), 'wb') as wav:
                wav.setnchannels(2)
                wav.setsampwidth(2)
                wav.setframerate(48000)
                wav.writeframes(pcm_data)
        except Exception as e:
            logger.error(f'Failed to write WAV file for {username}: {e}')
            return None
        
        # Calculate duration
        duration = len(pcm_data) / (48000 * 2 * 2)
        
        logger.info(
            f'✅ Saved {username}: {filename} '
            f'({duration:.1f}s, {len(pcm_data):,} bytes)'
        )
        
        return {
            'path': str(file_path),
            'size': len(pcm_data),
            'duration': duration,
            'filename': filename,
            'username': username
        }
    
    @staticmethod
    def _sanitize_filename(filename):
        """Create a safe filename from username"""
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in (' ', '-', '_'):
                safe_chars.append(char)
            elif char in ('/', '\\', ':', '*', '?', '"', '<', '>', '|'):
                safe_chars.append('_')
        
        result = ''.join(safe_chars).strip()
        result = result.replace(' ', '_')
        
        if not result:
            result = 'user'
        if len(result) > 50:
            result = result[:50]
        
        return result
    
    def get_statistics(self):
        """Get recording statistics"""
        total_bytes = sum(
            len(audio_data.file.getvalue())
            for audio_data in self.audio_data.values()
        )
        
        return {
            'user_count': len(self.audio_data),
            'total_bytes': total_bytes,
            'total_mb': total_bytes / (1024 * 1024),
            'session_duration': time.time() - self.session_start_time
        }