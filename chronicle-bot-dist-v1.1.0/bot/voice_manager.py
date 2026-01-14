"""
Voice Manager - Optimized voice connection and recording management

Handles voice connections, recording lifecycle, and coordination between
Discord voice and session management.
"""

import logging
from voice_receiver import VoiceReceiver

logger = logging.getLogger(__name__)


class VoiceManager:
    """
    Manages voice connections and recording sessions
    
    Features:
    - Voice connection lifecycle
    - Recording state tracking
    - Automatic cleanup
    - Error recovery
    """
    
    def __init__(self, bot, session_manager, audio_storage_path):
        """
        Initialize manager
        
        Args:
            bot: Discord bot instance
            session_manager: SessionManager instance
            audio_storage_path: Base path for audio storage
        """
        self.bot = bot
        self.session_manager = session_manager
        self.audio_storage_path = audio_storage_path
        self.receivers = {}  # session_id -> VoiceReceiver
        
        logger.info(f'VoiceManager initialized (storage={audio_storage_path})')
    
    async def start_recording(self, session_id, channel):
        """
        Start recording in a voice channel
        
        Args:
            session_id: Session UUID
            channel: Discord VoiceChannel
        
        Returns:
            VoiceReceiver: The recording voice client
        """
        logger.info(f'🎙️ Starting recording for session {session_id[:8]} in {channel.name}')
        
        try:
            # Check if already recording in this session
            if session_id in self.receivers:
                logger.warning(f'Session {session_id[:8]} already recording')
                return self.receivers[session_id]
            
            # Check if already connected to a channel in this guild
            existing_voice_client = channel.guild.voice_client
            if existing_voice_client:
                if existing_voice_client.channel.id == channel.id:
                    logger.info('Already connected to target channel')
                    receiver = existing_voice_client
                else:
                    logger.info(
                        f'Moving from {existing_voice_client.channel.name} to {channel.name}'
                    )
                    await existing_voice_client.disconnect()
                    receiver = await channel.connect(cls=VoiceReceiver)
            else:
                # Connect to voice channel
                receiver = await channel.connect(cls=VoiceReceiver)
            
            # Store receiver
            self.receivers[session_id] = receiver
            
            # Start recording
            await receiver.begin_recording(
                session_id,
                self.session_manager,
                self.audio_storage_path
            )
            
            logger.info(
                f'✅ Recording started for session {session_id[:8]}: '
                f'{receiver.get_participant_count()} participants'
            )
            
            return receiver
            
        except Exception as e:
            logger.error(f'Failed to start recording: {e}', exc_info=True)
            # Cleanup on error
            if session_id in self.receivers:
                del self.receivers[session_id]
            raise
    
    async def stop_recording(self, session_id):
        """
        Stop recording for a session
        
        Args:
            session_id: Session UUID
        
        Returns:
            list: List of saved audio file metadata
        """
        logger.info(f'⏹️ Stopping recording for session {session_id[:8]}')
        
        receiver = self.receivers.get(session_id)
        if not receiver:
            logger.warning(f'No receiver found for session {session_id[:8]}')
            return []
        
        try:
            # End recording
            audio_metadata = await receiver.end_recording()
            
            # Disconnect from voice
            await receiver.disconnect()
            
            # Remove from tracking
            del self.receivers[session_id]
            
            logger.info(
                f'✅ Recording stopped for session {session_id[:8]}: '
                f'{len(audio_metadata)} files saved'
            )
            
            return audio_metadata
            
        except Exception as e:
            logger.error(f'Error stopping recording: {e}', exc_info=True)
            # Still try to cleanup
            try:
                if receiver.is_connected():
                    await receiver.disconnect()
            except:
                pass
            
            if session_id in self.receivers:
                del self.receivers[session_id]
            
            return []
    
    async def stop_all_recordings(self):
        """
        Stop all active recordings (for shutdown)
        
        Returns:
            dict: {session_id: audio_metadata}
        """
        logger.info(f'Stopping all recordings ({len(self.receivers)} active)')
        
        results = {}
        
        for session_id, receiver in list(self.receivers.items()):
            try:
                audio_metadata = await self.stop_recording(session_id)
                results[session_id] = audio_metadata
            except Exception as e:
                logger.error(f'Error stopping session {session_id[:8]}: {e}')
                results[session_id] = []
        
        return results
    
    def get_active_sessions(self):
        """
        Get list of currently recording session IDs
        
        Returns:
            list: Session UUIDs
        """
        return list(self.receivers.keys())
    
    def is_recording(self, session_id):
        """
        Check if a session is currently recording
        
        Args:
            session_id: Session UUID
        
        Returns:
            bool: True if recording
        """
        return session_id in self.receivers
    
    def get_receiver(self, session_id):
        """
        Get the voice receiver for a session
        
        Args:
            session_id: Session UUID
        
        Returns:
            VoiceReceiver or None
        """
        return self.receivers.get(session_id)
    
    async def get_connection_info(self, guild_id):
        """
        Get voice connection info for a guild
        
        Args:
            guild_id: Discord guild ID
        
        Returns:
            dict: Connection information or None
        """
        for session_id, receiver in self.receivers.items():
            if receiver.guild.id == guild_id:
                return {
                    'session_id': session_id,
                    'channel': receiver.channel.name,
                    'participants': receiver.get_participant_count(),
                    'is_connected': receiver.is_connected(),
                    'is_recording': receiver.is_recording_active
                }
        return None
