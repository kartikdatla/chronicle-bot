"""
Transcription Orchestrator - Manages transcription jobs
"""

import asyncio
import logging
from datetime import datetime
from whisper_provider import WhisperProvider

logger = logging.getLogger(__name__)

class TranscriptionOrchestrator:
    """Manages async transcription jobs"""
    
    def __init__(self, db_pool):
        self.db = db_pool
        self.whisper = WhisperProvider(model_size='base')
        logger.info('Transcription orchestrator initialized')
    
    async def transcribe_session(self, session_id):
        """Transcribe all audio files for a session"""
        logger.info(f'Starting transcription for session {session_id}')
        
        # Get all audio files for this session
        async with self.db.acquire() as conn:
            audio_files = await conn.fetch('''
                SELECT id, file_path, user_id
                FROM audio_files
                WHERE session_id = $1
            ''', session_id)
        
        if not audio_files:
            logger.warning(f'No audio files found for session {session_id}')
            return []
        
        results = []
        
        for audio_file in audio_files:
            job_id = None
            try:
                # Create transcription job
                job_id = await self._create_job(session_id, audio_file['id'])
                
                # Transcribe (runs in thread pool to avoid blocking)
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    self.whisper.transcribe_sync,  # Use sync version
                    audio_file['file_path']
                )
                
                # Save result
                await self._complete_job(job_id, result)
                
                results.append({
                    'user_id': audio_file['user_id'],
                    'text': result['text'],
                    'job_id': job_id
                })
                
                logger.info(f'Transcribed audio for user {audio_file["user_id"]}')
                
            except Exception as e:
                logger.error(f'Failed to transcribe {audio_file["file_path"]}: {e}')
                if job_id:
                    await self._fail_job(job_id, str(e))
        
        logger.info(f'Session {session_id} transcription complete: {len(results)}/{len(audio_files)} succeeded')
        return results
    
    async def _create_job(self, session_id, audio_file_id):
        """Create transcription job record"""
        async with self.db.acquire() as conn:
            job_id = await conn.fetchval('''
                INSERT INTO transcription_jobs
                (session_id, audio_file_id, status, provider, created_at)
                VALUES ($1, $2, 'processing', 'whisper_local', $3)
                RETURNING id
            ''', session_id, audio_file_id, datetime.utcnow())
        
        return job_id
    
    async def _complete_job(self, job_id, result):
        """Mark job as completed with results"""
        async with self.db.acquire() as conn:
            await conn.execute('''
                UPDATE transcription_jobs
                SET status = 'completed',
                    transcript_text = $1,
                    confidence = $2,
                    processing_time = $3,
                    completed_at = $4
                WHERE id = $5
            ''', result['text'], result['confidence'], 
                result['processing_time'], datetime.utcnow(), job_id)
    
    async def _fail_job(self, job_id, error_message):
        """Mark job as failed"""
        async with self.db.acquire() as conn:
            await conn.execute('''
                UPDATE transcription_jobs
                SET status = 'failed',
                    error_message = $1,
                    completed_at = $2
                WHERE id = $3
            ''', error_message, datetime.utcnow(), job_id)
