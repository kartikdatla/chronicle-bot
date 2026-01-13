"""
Session Manager - Optimized database operations

Handles all session-related database operations with proper connection pooling,
error handling, and query optimization.
"""

import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages RPG recording sessions in the database
    
    Features:
    - Connection pooling
    - Prepared statements for performance
    - Transaction management
    - Comprehensive error handling
    """
    
    def __init__(self, db_pool):
        """
        Initialize manager
        
        Args:
            db_pool: asyncpg connection pool
        """
        self.db = db_pool
        logger.info('SessionManager initialized')
    
    async def create_session(self, guild_id, channel_id, creator_id, name=None):
        """
        Create a new recording session
        
        Args:
            guild_id: Discord guild ID
            channel_id: Voice channel ID
            creator_id: User who started the session
            name: Optional session name
        
        Returns:
            str: Session UUID
        """
        session_id = str(uuid.uuid4())
        
        try:
            async with self.db.acquire() as conn:
                await conn.execute('''
                    INSERT INTO sessions (
                        id, guild_id, channel_id, creator_id, name, 
                        status, start_time
                    )
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''',
                    session_id,
                    guild_id,
                    channel_id,
                    creator_id,
                    name,
                    'active',
                    datetime.utcnow()
                )
            
            logger.info(
                f'✅ Created session {session_id[:8]} in guild {guild_id} '
                f'(name={name or "Unnamed"})'
            )
            
            return session_id
            
        except Exception as e:
            logger.error(f'Failed to create session: {e}', exc_info=True)
            raise
    
    async def get_active_session(self, guild_id):
        """
        Get the currently active session for a guild
        
        Args:
            guild_id: Discord guild ID
        
        Returns:
            str: Session UUID or None
        """
        try:
            async with self.db.acquire() as conn:
                result = await conn.fetchval('''
                    SELECT id FROM sessions
                    WHERE guild_id = $1 AND status = 'active'
                    ORDER BY start_time DESC
                    LIMIT 1
                ''', guild_id)
            
            if result:
                logger.debug(f'Found active session {str(result)[:8]} for guild {guild_id}')
            
            return str(result) if result else None
            
        except Exception as e:
            logger.error(f'Failed to get active session: {e}', exc_info=True)
            return None
    
    async def end_session(self, session_id):
        """
        Mark a session as completed
        
        Args:
            session_id: Session UUID
        """
        try:
            async with self.db.acquire() as conn:
                result = await conn.execute('''
                    UPDATE sessions
                    SET status = 'completed',
                        end_time = $1
                    WHERE id = $2 AND status = 'active'
                ''', datetime.utcnow(), uuid.UUID(session_id))
            
            if result == 'UPDATE 0':
                logger.warning(f'Session {session_id[:8]} not found or already ended')
            else:
                logger.info(f'✅ Ended session {session_id[:8]}')
            
        except Exception as e:
            logger.error(f'Failed to end session: {e}', exc_info=True)
            raise
    
    async def add_participant(self, session_id, user_id):
        """
        Add a participant to a session
        
        Args:
            session_id: Session UUID
            user_id: Discord user ID
        """
        try:
            async with self.db.acquire() as conn:
                # Check if already exists
                exists = await conn.fetchval('''
                    SELECT 1 FROM participants
                    WHERE session_id = $1 AND user_id = $2
                ''', uuid.UUID(session_id), user_id)
                
                if exists:
                    logger.debug(f'Participant {user_id} already in session')
                    return
                
                # Insert new participant
                await conn.execute('''
                    INSERT INTO participants (session_id, user_id, joined_at)
                    VALUES ($1, $2, $3)
                ''', uuid.UUID(session_id), user_id, datetime.utcnow())
            
            logger.debug(f'Added participant {user_id} to session {session_id[:8]}')
            
        except Exception as e:
            logger.error(f'Failed to add participant: {e}', exc_info=True)
            # Don't raise - this shouldn't break the recording
    
    async def save_audio_file(self, session_id, user_id, file_path, duration, size):
        """
        Save audio file metadata to database
        
        Args:
            session_id: Session UUID
            user_id: Discord user ID
            file_path: Path to audio file
            duration: Duration in seconds
            size: File size in bytes
        """
        try:
            async with self.db.acquire() as conn:
                await conn.execute('''
                    INSERT INTO audio_files (
                        session_id, user_id, file_path, 
                        duration, file_size, created_at
                    )
                    VALUES ($1, $2, $3, $4, $5, $6)
                ''',
                    uuid.UUID(session_id),
                    user_id,
                    file_path,
                    duration,
                    size,
                    datetime.utcnow()
                )
            
            logger.debug(
                f'Saved audio file metadata: user={user_id}, '
                f'duration={duration:.1f}s, size={size} bytes'
            )
            
        except Exception as e:
            logger.error(f'Failed to save audio file metadata: {e}', exc_info=True)
            # Don't raise - file is already saved to disk
    
    async def get_session_details(self, session_id):
        """
        Get detailed information about a session
        
        Args:
            session_id: Session UUID
        
        Returns:
            dict: Session details including participants and files
        """
        try:
            async with self.db.acquire() as conn:
                # Get session
                session = await conn.fetchrow('''
                    SELECT * FROM sessions WHERE id = $1
                ''', uuid.UUID(session_id))
                
                if not session:
                    return None
                
                # Get participants
                participants = await conn.fetch('''
                    SELECT user_id, joined_at FROM participants
                    WHERE session_id = $1
                    ORDER BY joined_at
                ''', uuid.UUID(session_id))
                
                # Get audio files
                audio_files = await conn.fetch('''
                    SELECT user_id, file_path, duration, file_size
                    FROM audio_files
                    WHERE session_id = $1
                    ORDER BY user_id
                ''', uuid.UUID(session_id))
                
                return {
                    'session': dict(session),
                    'participants': [dict(p) for p in participants],
                    'audio_files': [dict(a) for a in audio_files]
                }
            
        except Exception as e:
            logger.error(f'Failed to get session details: {e}', exc_info=True)
            return None
    
    async def get_guild_sessions(self, guild_id, limit=10, status=None):
        """
        Get recent sessions for a guild
        
        Args:
            guild_id: Discord guild ID
            limit: Maximum number of sessions
            status: Optional status filter ('active', 'completed')
        
        Returns:
            list: List of session dictionaries
        """
        try:
            async with self.db.acquire() as conn:
                if status:
                    query = '''
                        SELECT id, name, status, start_time, end_time
                        FROM sessions
                        WHERE guild_id = $1 AND status = $2
                        ORDER BY start_time DESC
                        LIMIT $3
                    '''
                    sessions = await conn.fetch(query, guild_id, status, limit)
                else:
                    query = '''
                        SELECT id, name, status, start_time, end_time
                        FROM sessions
                        WHERE guild_id = $1
                        ORDER BY start_time DESC
                        LIMIT $2
                    '''
                    sessions = await conn.fetch(query, guild_id, limit)
                
                return [dict(s) for s in sessions]
            
        except Exception as e:
            logger.error(f'Failed to get guild sessions: {e}', exc_info=True)
            return []
    
    async def cleanup_old_sessions(self, days=30):
        """
        Clean up old sessions (for maintenance)
        
        Args:
            days: Delete sessions older than this many days
        
        Returns:
            int: Number of sessions deleted
        """
        try:
            async with self.db.acquire() as conn:
                result = await conn.execute('''
                    DELETE FROM sessions
                    WHERE end_time < NOW() - INTERVAL '%s days'
                    AND status = 'completed'
                ''', days)
                
                # Extract count from result string "DELETE N"
                count = int(result.split()[1]) if result else 0
                
                if count > 0:
                    logger.info(f'Cleaned up {count} old sessions')
                
                return count
            
        except Exception as e:
            logger.error(f'Failed to cleanup old sessions: {e}', exc_info=True)
            return 0
