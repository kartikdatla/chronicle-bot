"""
Per-User Audio Sink - Optimized version

Captures per-user audio streams and saves them as individual WAV files
with proper error handling and validation.
"""

import discord
import wave
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class PerUserWavSink(discord.sinks.Sink):
    """
    Pycord sink that saves per-user audio to separate WAV files
    
    Features:
    - Individual files per participant
    - Readable filenames (username_timestamp.wav)
    - Proper error handling
    - Audio validation
    """
    
    def __init__(self, output_dir, session_id, participants):
        """
        Initialize sink
        
        Args:
            output_dir: Base output directory
            session_id: Session UUID
            participants: List of Discord Member objects
        """
        super().__init__()
        
        self.output_dir = Path(output_dir) / session_id
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = session_id
        self.participants = {p.id: p for p in participants}  # Map user_id -> Member
        
        logger.info(
            f'PerUserWavSink initialized: session={session_id[:8]}, '
            f'participants={len(participants)}, path={self.output_dir}'
        )
    
    def cleanup(self):
        """
        Save all recorded audio to individual WAV files
        
        Returns:
            dict: {user_id: {path, size, duration}} for successfully saved files
        """
        logger.info(f'🎵 Saving audio for {len(self.audio_data)} users')
        
        if not self.audio_data:
            logger.warning('No audio data to save')
            return {}
        
        saved_files = {}
        errors = []
        
        for user_id, audio_data in self.audio_data.items():
            try:
                result = self._save_user_audio(user_id, audio_data)
                if result:
                    saved_files[user_id] = result
            except Exception as e:
                error_msg = f'Failed to save audio for user {user_id}: {e}'
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)
        
        # Log summary
        if saved_files:
            logger.info(f'✅ Successfully saved {len(saved_files)} audio files')
        
        if errors:
            logger.warning(f'⚠️ {len(errors)} files failed to save')
        
        return saved_files
    
    def _save_user_audio(self, user_id, audio_data):
        """
        Save audio for a single user
        
        Args:
            user_id: Discord user ID
            audio_data: AudioData object from Pycord
        
        Returns:
            dict: {path, size, duration} or None if failed
        """
        # Get user info
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
        
        if len(pcm_data) < 1000:  # Less than ~0.01 seconds
            logger.warning(f'Audio too short for {username}, skipping')
            return None
        
        # Create safe filename
        clean_name = self._sanitize_filename(username)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        filename = f'{clean_name}_{timestamp}.wav'
        file_path = self.output_dir / filename
        
        # Write WAV file
        try:
            with wave.open(str(file_path), 'wb') as wav:
                wav.setnchannels(2)  # Stereo
                wav.setsampwidth(2)  # 16-bit
                wav.setframerate(48000)  # 48kHz
                wav.writeframes(pcm_data)
        except Exception as e:
            logger.error(f'Failed to write WAV file for {username}: {e}')
            return None
        
        # Calculate duration
        # Duration = bytes / (sample_rate * channels * sample_width)
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
        """
        Create a safe filename from username
        
        Args:
            filename: Raw username
        
        Returns:
            str: Sanitized filename
        """
        # Remove or replace unsafe characters
        safe_chars = []
        for char in filename:
            if char.isalnum() or char in (' ', '-', '_'):
                safe_chars.append(char)
            elif char in ('/', '\\', ':', '*', '?', '"', '<', '>', '|'):
                safe_chars.append('_')
        
        result = ''.join(safe_chars).strip()
        
        # Replace spaces with underscores
        result = result.replace(' ', '_')
        
        # Ensure not empty and not too long
        if not result:
            result = 'user'
        if len(result) > 50:
            result = result[:50]
        
        return result
    
    def get_statistics(self):
        """
        Get recording statistics
        
        Returns:
            dict: Statistics about recorded audio
        """
        total_bytes = sum(
            len(audio_data.file.getvalue())
            for audio_data in self.audio_data.values()
        )
        
        return {
            'user_count': len(self.audio_data),
            'total_bytes': total_bytes,
            'total_mb': total_bytes / (1024 * 1024)
        }
