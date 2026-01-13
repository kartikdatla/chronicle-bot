"""
Configuration - Centralized settings for Chronicle Bot
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
BOT_PREFIX = '/'

# Database Configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/rpg_sessions')
DB_MIN_POOL_SIZE = 2
DB_MAX_POOL_SIZE = 10

# Audio Configuration
AUDIO_STORAGE_PATH = Path(os.getenv('AUDIO_STORAGE_PATH', './data/audio'))
AUDIO_SAMPLE_RATE = 48000
AUDIO_CHANNELS = 2
AUDIO_SAMPLE_WIDTH = 2

# Transcription Configuration
WHISPER_MODEL = os.getenv('WHISPER_MODEL', 'base')  # tiny, base, small, medium, large
TRANSCRIPTION_THREAD_POOL_SIZE = 4

# AI Summary Configuration
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')
OLLAMA_TIMEOUT = 60  # seconds
SUMMARY_MIN_LENGTH = 300
SUMMARY_MAX_LENGTH = 500

# Export Configuration
TRANSCRIPT_OUTPUT_PATH = Path(os.getenv('TRANSCRIPT_OUTPUT_PATH', './data/transcripts'))
EXPORT_PAGE_SIZE = 'letter'  # letter or a4
EXPORT_MARGIN_INCHES = 1.0

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Feature Flags
ENABLE_AI_SUMMARY = os.getenv('ENABLE_AI_SUMMARY', 'true').lower() == 'true'
ENABLE_AUTO_TRANSCRIBE = os.getenv('ENABLE_AUTO_TRANSCRIBE', 'false').lower() == 'true'
ENABLE_SESSION_BACKUPS = os.getenv('ENABLE_SESSION_BACKUPS', 'true').lower() == 'true'

# Performance Configuration
MAX_RECORDING_DURATION = 3600 * 4  # 4 hours
MAX_FILE_SIZE_MB = 500
CLEANUP_OLD_SESSIONS_DAYS = 30

# Create directories
AUDIO_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
TRANSCRIPT_OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

def validate_config():
    """Validate configuration on startup"""
    errors = []
    
    # Token validation skipped - handled in main.py with fallback
    
    if not DATABASE_URL:
        errors.append("DATABASE_URL not set")
    
    if WHISPER_MODEL not in ['tiny', 'base', 'small', 'medium', 'large']:
        errors.append(f"Invalid WHISPER_MODEL: {WHISPER_MODEL}")
    
    if errors:
        raise ValueError("Configuration errors:\n" + "\n".join(errors))
    
    return True
