import discord
import asyncio
import logging
from per_user_sink import PerUserWavSink

logger = logging.getLogger(__name__)

class VoiceReceiver(discord.VoiceClient):
    def __init__(self, client, channel):
        super().__init__(client, channel)
        self.recording_session_id = None
        self.recording_session_manager = None
        self.recording_output_dir = None
        self.is_recording_active = False
        self.participants = []
        self.saved_files_info = []
        self.sink = None
    
    async def begin_recording(self, session_id, session_manager, output_dir):
        self.recording_session_id = session_id
        self.recording_session_manager = session_manager
        self.recording_output_dir = output_dir
        self.is_recording_active = True
        
        logger.info(f'🎙️ Starting Pycord recording for session {session_id[:8]}')
        
        for member in self.channel.members:
            if not member.bot:
                self.participants.append(member)
                await session_manager.add_participant(session_id, member.id)
        
        self.sink = PerUserWavSink(output_dir, session_id, self.participants)
        
        def sync_callback_wrapper(sink, *args):
            asyncio.run_coroutine_threadsafe(
                self._async_save_handler(sink),
                self.loop
            )
        
        self.start_recording(self.sink, sync_callback_wrapper, self.channel)
        logger.info(f'✅ Recording started: {len(self.participants)} participants in {self.channel.name}')
    
    async def _async_save_handler(self, sink):
        try:
            logger.info(f'💾 Saving audio files for session {self.recording_session_id[:8]}')
            saved_files = sink.cleanup()
            
            if not saved_files:
                return
            
            self.saved_files_info = []
            
            for user_id, file_info in saved_files.items():
                try:
                    await self.recording_session_manager.save_audio_file(
                        self.recording_session_id,
                        user_id,
                        file_info['path'],
                        file_info['duration'],
                        file_info['size']
                    )
                    self.saved_files_info.append(file_info)
                except Exception as e:
                    logger.error(f'Failed to save metadata: {e}')
            
            logger.info(f'✅ Audio save complete')
        except Exception as e:
            logger.error(f'Error in save handler: {e}', exc_info=True)
    
    async def end_recording(self):
        if not self.is_recording_active:
            return []
        
        self.is_recording_active = False
        logger.info(f'⏹️ Stopping recording')
        
        try:
            self.stop_recording()
            await asyncio.sleep(2.5)
            return self.saved_files_info
        except Exception as e:
            logger.error(f'Error ending: {e}')
            return self.saved_files_info
    
    def get_participant_count(self):
        return len(self.participants)
