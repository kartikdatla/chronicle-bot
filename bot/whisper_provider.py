"""
Whisper Local Provider - Free transcription using local Whisper
"""
import whisper
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)

class WhisperProvider:
    """Local Whisper transcription provider"""
    
    def __init__(self, model_size='base'):
        """Initialize Whisper model"""
        self.model_size = model_size
        self.model = None
        self.name = 'whisper_local'
        logger.info(f'Whisper provider initialized (model: {model_size})')
    
    def load_model(self):
        """Load the Whisper model (lazy loading)"""
        if self.model is None:
            logger.info(f'Loading Whisper {self.model_size} model...')
            self.model = whisper.load_model(self.model_size)
            logger.info('Whisper model loaded')
    
    def transcribe_audio(self, file_path):
        """Transcribe audio file with word timestamps"""
        self.load_model()
        logger.info(f'Transcribing: {file_path}')
        
        result = self.model.transcribe(
            str(file_path),
            language='en',
            task='transcribe',
            verbose=False
        )
        
        return result['text'].strip()
    
    def transcribe_sync(self, audio_path):
        """Transcribe audio file (synchronous version for thread pool)"""
        self.load_model()
        logger.info(f'Transcribing: {audio_path}')
        start_time = time.time()
        
        try:
            result = self.model.transcribe(
                str(audio_path),
                language='en',
                task='transcribe',
                verbose=False
            )
            
            processing_time = time.time() - start_time
            
            segments = result.get('segments', [])
            if segments:
                avg_confidence = sum(s.get('no_speech_prob', 0) for s in segments) / len(segments)
                confidence = 1.0 - avg_confidence
            else:
                confidence = 0.0
            
            logger.info(f'Transcription complete in {processing_time:.1f}s')
            
            return {
                'text': result['text'].strip(),
                'confidence': confidence,
                'processing_time': processing_time,
                'provider': self.name
            }
        except Exception as e:
            logger.error(f'Transcription failed: {e}')
            raise
