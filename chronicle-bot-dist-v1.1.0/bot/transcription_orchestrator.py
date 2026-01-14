"""
Transcription Orchestrator with Timestamp-Based Ordering

Processes audio files and orders transcripts chronologically
"""

import logging
import json
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class TranscriptionOrchestrator:
    """Manages transcription workflow with chronological ordering"""
    
    def __init__(self, db_pool):
        self.db = db_pool
        
        # Import here to avoid circular dependency
        from whisper_provider import WhisperProvider
        self.whisper = WhisperProvider()
        
        logger.info('Transcription orchestrator initialized')
    
    async def transcribe_session(self, session_id):
        """
        Transcribe all audio files for a session and order chronologically
        
        Returns:
            list: Chronologically ordered transcript segments
        """
        logger.info(f'Starting transcription for session {session_id}')
        
        try:
            # Get audio files for this session
            async with self.db.acquire() as conn:
                audio_files = await conn.fetch('''
                    SELECT user_id, file_path, duration
                    FROM audio_files
                    WHERE session_id = $1
                    ORDER BY created_at
                ''', session_id)
            
            if not audio_files:
                logger.warning(f'No audio files found for session {session_id}')
                return []
            
            # Load timestamp metadata if available
            session_dir = Path(audio_files[0]['file_path']).parent
            timestamp_metadata = self._load_timestamp_metadata(session_dir)
            
            # Transcribe each audio file
            all_segments = []
            succeeded = 0
            
            for audio_file in audio_files:
                user_id = audio_file['user_id']
                file_path = audio_file['file_path']
                
                # Convert to absolute path if relative
                if not Path(file_path).is_absolute():
                    file_path = str(Path.cwd() / file_path)
                
                try:
                    # Transcribe audio
                    text = await asyncio.to_thread(self.whisper.transcribe_audio, file_path)
                    
                    if not text or not text.strip():
                        logger.warning(f'Empty transcription for user {user_id}')
                        continue
                    
                    # Fix fantasy names
                    text = self._fix_fantasy_names(text)
                    
                    # Save to database
                    await self._save_transcription(session_id, user_id, file_path, text)
                    
                    # If we have timestamp data, break into segments
                    if timestamp_metadata and str(user_id) in timestamp_metadata:
                        segments = self._create_segments_with_timestamps(
                            user_id,
                            text,
                            timestamp_metadata[str(user_id)],
                            audio_file['duration']
                        )
                        all_segments.extend(segments)
                    else:
                        # No timestamp data, treat as single segment
                        all_segments.append({
                            'user_id': user_id,
                            'text': text.strip(),
                            'timestamp': 0.0,
                            'duration': audio_file['duration']
                        })
                    
                    succeeded += 1
                    logger.info(f'Transcribed audio for user {user_id}')
                    
                except Exception as e:
                    logger.error(f'Failed to transcribe for user {user_id}: {e}', exc_info=True)
            
            # Sort all segments by timestamp
            all_segments.sort(key=lambda x: x['timestamp'])
            
            logger.info(
                f'Session {session_id} transcription complete: '
                f'{succeeded}/{len(audio_files)} succeeded, '
                f'{len(all_segments)} segments ordered chronologically'
            )
            
            return all_segments
            
        except Exception as e:
            logger.error(f'Transcription failed for session {session_id}: {e}', exc_info=True)
            return []
    
    def _load_timestamp_metadata(self, session_dir):
        """Load timestamp metadata from JSON file"""
        metadata_path = Path(session_dir) / 'timestamps.json'
        
        if not metadata_path.exists():
            logger.info('No timestamp metadata found, using default ordering')
            return {}
        
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
            logger.info(f'Loaded timestamp metadata for {len(metadata)} users')
            return metadata
        except Exception as e:
            logger.error(f'Failed to load timestamp metadata: {e}')
            return {}
    
    def _create_segments_with_timestamps(self, user_id, full_text, metadata, total_duration):
        """
        Split transcription into segments based on audio timestamps
        Uses actual recorded timestamps to estimate when each sentence was spoken
        """
        timestamps = metadata.get('timestamps', [])
        
        if not timestamps:
            # No timestamp data, return as single segment
            return [{
                'user_id': user_id,
                'text': full_text.strip(),
                'timestamp': 0.0,
                'duration': total_duration
            }]
        
        # Split text into sentences
        sentences = self._split_into_sentences(full_text)
        
        if not sentences:
            return [{
                'user_id': user_id,
                'text': full_text.strip(),
                'timestamp': timestamps[0][0] if timestamps else 0.0,
                'duration': total_duration
            }]
        
        # Calculate actual recording span
        first_timestamp = timestamps[0][0]  # When recording started for this user
        last_timestamp = timestamps[-1][0]  # When last chunk was recorded
        recording_span = last_timestamp - first_timestamp
        
        # If recording span is too small, fall back to simple distribution
        if recording_span < 1.0:
            recording_span = total_duration
        
        # Distribute sentences evenly across the actual recording time
        segments = []
        time_per_sentence = recording_span / len(sentences)
        
        for i, sentence in enumerate(sentences):
            # Calculate timestamp for this sentence
            sentence_timestamp = first_timestamp + (i * time_per_sentence)
            
            segments.append({
                'user_id': user_id,
                'text': sentence.strip(),
                'timestamp': sentence_timestamp,
                'duration': time_per_sentence
            })
        
        return segments
    
    def _split_into_sentences(self, text):
        """Split text into sentences for better chronological ordering"""
        import re
        sentences = re.split(r'[.!?]+\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences
    
    def _fix_fantasy_names(self, text):
        """Fix commonly misheard fantasy names"""
        replacements = {
            'algorithm star': 'Alkenstar',
            'algo star': 'Alkenstar',
            'alistair': 'Alkenstar',
            'our gun staff': 'Alkenstar',
            'our gun star': 'Alkenstar',
            'arkansas': 'Alkenstar',
            'next us': 'Nexan',
            'lighter college': 'Blythe College',
            'blightier college': 'Blythe College',
            'life at college': 'Blythe College',
            'man away': 'Mana Waste',
            'manaways': 'Mana Waste',
            'gun works': 'Gunworks',
            'shape of modules': 'Shield Marshals',
            'shield martial': 'Shield Marshal',
            'mugland': 'Mugland',
            'gab': 'Gibb',
            'alcan star': 'Alkenstar',
            'kept': 'Capt',
        }
        
        for wrong, right in replacements.items():
            # Case-insensitive replacement
            import re
            text = re.sub(re.escape(wrong), right, text, flags=re.IGNORECASE)
        
        return text
    
    async def _save_transcription(self, session_id, user_id, file_path, text):
        """Save transcription to database"""
        try:
            async with self.db.acquire() as conn:
                # Get the audio_file_id first
                audio_file_id = await conn.fetchval('''
                    SELECT id FROM audio_files
                    WHERE session_id = $1 AND user_id = $2
                    LIMIT 1
                ''', session_id, user_id)
                
                if audio_file_id:
                    await conn.execute('''
                        INSERT INTO transcription_jobs (
                            session_id, audio_file_id, transcript_text,
                            status, created_at, completed_at
                        )
                        VALUES ($1, $2, $3, $4, NOW(), NOW())
                    ''', session_id, audio_file_id, text, 'completed')
                else:
                    logger.warning(f'No audio_file_id found for user {user_id}')
        except Exception as e:
            logger.error(f'Failed to save transcription: {e}')
            raise