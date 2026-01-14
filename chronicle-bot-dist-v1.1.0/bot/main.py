"""
Discord RPG Transcription Bot - Production Ready
Compatible with existing infrastructure
"""

import os
import sys
import logging
import signal
import asyncio
import discord
from pathlib import Path
from dotenv import load_dotenv

# Add bot directory to path
BOT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BOT_DIR))

# Load environment
load_dotenv()

# Import managers
from session_manager import SessionManager
from voice_manager import VoiceManager
from transcription_orchestrator import TranscriptionOrchestrator
from transcript_formatter import TranscriptFormatter
from summary_generator import SummaryGenerator

# Configure logging with UTF-8 support
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Create bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True
intents.members = True

bot = discord.Bot(intents=intents)

# Global managers
session_manager = None
voice_manager = None
transcription_orchestrator = None
transcript_formatter = None
summary_generator = None
db_pool = None


async def graceful_shutdown():
    """Gracefully shutdown the bot"""
    logger.info('Initiating graceful shutdown...')
    
    try:
        if voice_manager:
            for session_id, receiver in list(voice_manager.receivers.items()):
                try:
                    await voice_manager.stop_recording(session_id)
                except:
                    pass
        
        if db_pool:
            await db_pool.close()
            logger.info('Database connections closed')
        
        await bot.close()
        logger.info('Bot shut down successfully')
        
    except Exception as e:
        logger.error(f'Error during shutdown: {e}')


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f'Received signal {signum}')
    asyncio.create_task(graceful_shutdown())


@bot.event
async def on_ready():
    """Initialize bot systems"""
    global session_manager, voice_manager, transcription_orchestrator
    global transcript_formatter, summary_generator, db_pool
    
    logger.info(f'Bot: {bot.user} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    try:
        # Initialize database
        import asyncpg
        db_pool = await asyncpg.create_pool(
            os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/rpg_sessions'),
            min_size=2,
            max_size=10,
            command_timeout=60
        )
        logger.info('Database pool created')
        
        # Initialize managers - COMPATIBLE WITH EXISTING CODE
        session_manager = SessionManager(db_pool)
        voice_manager = VoiceManager(bot, session_manager, './data/audio')
        transcription_orchestrator = TranscriptionOrchestrator(db_pool)  # Only db_pool
        transcript_formatter = TranscriptFormatter('./data/transcripts')
        summary_generator = SummaryGenerator('llama3.2:3b', './data/transcripts')
        
        logger.info('All systems initialized')
        
        # Set bot status
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.listening,
                name='RPG sessions | /start'
            )
        )
        
        logger.info('Bot ready!')
        
    except Exception as e:
        logger.error(f'Initialization failed: {e}', exc_info=True)
        await graceful_shutdown()
        sys.exit(1)


@bot.event
async def on_voice_state_update(member, before, after):
    """Track users joining/leaving voice"""
    if member.bot or not session_manager:
        return
    
    try:
        session_id = await session_manager.get_active_session(member.guild.id)
        if not session_id:
            return
        
        receiver = voice_manager.receivers.get(session_id)
        if not receiver:
            return
        
        # User joined
        if after.channel and after.channel.id == receiver.channel.id:
            if not before.channel or before.channel.id != receiver.channel.id:
                await session_manager.add_participant(session_id, member.id)
                if member not in receiver.participants:
                    receiver.participants.append(member)
                logger.info(f'{member.name} joined session {session_id[:8]}')
        
        # User left
        elif before.channel and before.channel.id == receiver.channel.id:
            if member in receiver.participants:
                receiver.participants.remove(member)
            logger.info(f'{member.name} left session {session_id[:8]}')
    
    except Exception as e:
        logger.error(f'Error in voice_state_update: {e}')


@bot.slash_command(name='ping', description='Check bot latency')
async def ping_cmd(ctx: discord.ApplicationContext):
    await ctx.respond(f'Pong! {round(bot.latency * 1000)}ms')


@bot.slash_command(name='start', description='Start recording')
async def start_cmd(
    ctx: discord.ApplicationContext,
    name: discord.Option(str, description='Session name', required=False) = None
):
    if not session_manager:
        await ctx.respond('Bot initializing...', ephemeral=True)
        return
    
    if not ctx.author.voice:
        await ctx.respond('Join a voice channel first!', ephemeral=True)
        return
    
    if await session_manager.get_active_session(ctx.guild_id):
        await ctx.respond('Session already active! Use /stop first.', ephemeral=True)
        return
    
    await ctx.defer()
    
    try:
        session_id = await session_manager.create_session(
            guild_id=ctx.guild_id,
            channel_id=ctx.author.voice.channel.id,
            creator_id=ctx.author.id,
            name=name
        )
        
        await voice_manager.start_recording(session_id, ctx.author.voice.channel)
        
        participant_count = len([m for m in ctx.author.voice.channel.members if not m.bot])
        
        await ctx.followup.send(
            f'🎙️ **Recording Started**\n'
            f'Session: `{session_id[:8]}...`\n'
            f'Channel: {ctx.author.voice.channel.mention}\n'
            f'Participants: {participant_count}\n\n'
            f'Use `/stop` when finished.'
        )
        
        logger.info(f'Started session {session_id[:8]} in {ctx.guild.name}')
        
    except Exception as e:
        logger.error(f'Start failed: {e}', exc_info=True)
        await ctx.followup.send(f'Error: {e}', ephemeral=True)


@bot.slash_command(name='stop', description='Stop recording')
async def stop_cmd(ctx: discord.ApplicationContext):
    if not session_manager:
        await ctx.respond('Bot initializing...', ephemeral=True)
        return
    
    session_id = await session_manager.get_active_session(ctx.guild_id)
    if not session_id:
        await ctx.respond('No active session.', ephemeral=True)
        return
    
    await ctx.defer()
    
    try:
        audio_metadata = await voice_manager.stop_recording(session_id)
        await session_manager.end_session(session_id)
        
        total_duration = sum(a['duration'] for a in audio_metadata) if audio_metadata else 0
        total_size = sum(a['size'] for a in audio_metadata) if audio_metadata else 0
        
        await ctx.followup.send(
            f'⏹️ **Recording Stopped**\n'
            f'Session: `{session_id[:8]}...`\n'
            f'Participants: {len(audio_metadata)}\n'
            f'Duration: {total_duration/60:.1f} minutes\n'
            f'Size: {total_size/1024/1024:.1f} MB\n\n'
            f'Use `/transcribe` to generate transcript.'
        )
        
        logger.info(f'Stopped session {session_id[:8]}')
        
    except Exception as e:
        logger.error(f'Stop failed: {e}', exc_info=True)
        await ctx.followup.send(f'Error: {e}', ephemeral=True)


@bot.slash_command(name='transcribe', description='Transcribe and summarize')
async def transcribe_cmd(ctx: discord.ApplicationContext):
    if not transcription_orchestrator:
        await ctx.respond('Bot initializing...', ephemeral=True)
        return
    
    await ctx.defer()
    
    try:
        async with session_manager.db.acquire() as conn:
            session = await conn.fetchrow('''
                SELECT id, name FROM sessions
                WHERE guild_id = $1 AND status = 'completed'
                ORDER BY end_time DESC LIMIT 1
            ''', ctx.guild_id)
        
        if not session:
            await ctx.followup.send('No completed sessions found.')
            return
        
        session_id = str(session['id'])
        session_name = session['name']
        
        progress_msg = await ctx.followup.send(
            f'🔄 **Processing Session**\n'
            f'Name: {session_name or "Unnamed"}\n\n'
            f'⏳ Step 1/3: Transcribing audio...'
        )
        
        # Transcribe
        segments = await transcription_orchestrator.transcribe_session(session_id)
        
        if not segments:
            await progress_msg.edit(content='No audio found.')
            return
        
        # Count unique users who actually spoke
        unique_users = len(set(seg['user_id'] for seg in segments))
        
        await progress_msg.edit(
            content=f'🔄 **Processing Session**\n'
                    f'✅ Step 1/3: Transcribed {unique_users} participants\n'
                    f'⏳ Step 2/3: Generating transcript document...'
        )
        
      # Build transcript data and collect unique participants
        user_names = {}
        transcript_data = []
        
        for seg in segments:
            user_id = seg['user_id']
            
            # Get username once per user (cache it)
            if user_id not in user_names:
                member = ctx.guild.get_member(user_id)
                user_names[user_id] = member.name if member else f"User {user_id}"
            
            transcript_data.append({
                'user_id': user_id,
                'user_name': user_names[user_id],
                'text': seg['text'],
                'timestamp': seg.get('timestamp', 0)
            })
        
        # Create unique, sorted participants list
        participants = sorted(list(set(user_names.values())))
        
        # Create unique, sorted participants list
        participants = sorted(list(set(user_names.values())))
        
        # Export transcript
        transcript_path = await transcript_formatter.export_transcript(
            session_id,
            session_name,
            transcript_data,
            participants
        )
        
        await progress_msg.edit(
            content=f'🔄 **Processing Session**\n'
                    f'✅ Step 1/3: Transcribed {unique_users} participants\n'
                    f'✅ Step 2/3: Transcript document created\n'
                    f'⏳ Step 3/3: Generating AI summary...'
        )
        
        # Generate AI summary
        try:
            summary_path = await summary_generator.generate_summary(
                session_id,
                transcript_data,
                session_name
            )
            summary_status = '✅ Step 3/3: AI summary generated'
        except Exception as e:
            logger.error(f'AI summary failed: {e}')
            summary_path = None
            summary_status = '⚠️ Step 3/3: AI summary failed'
        
        # Preview
        preview = '\n'.join([
            f'**{t["user_name"]}:** {t["text"][:80]}{"..." if len(t["text"]) > 80 else ""}'
            for t in transcript_data[:2]
        ])
        
        result_message = (
            f'✅ **Processing Complete!**\n\n'
            f'{preview}\n\n'
            f'📄 **Transcript:** `{transcript_path}`\n'
        )
        
        if summary_path:
            result_message += f'📖 **Summary:** `{summary_path}`\n'
        
        result_message += f'\n💾 Files saved to: `data/transcripts/{session_id[:8]}...`'
        
        await progress_msg.edit(content=result_message)
        
        logger.info(f'Transcribed session {session_id[:8]}')
        
    except Exception as e:
        logger.error(f'Transcription failed: {e}', exc_info=True)
        await ctx.channel.send(f'❌ **Transcription Failed**\nError: ```{str(e)}```')


@bot.slash_command(name='status', description='Show bot status')
async def status_cmd(ctx: discord.ApplicationContext):
    await ctx.defer()
    
    try:
        async with session_manager.db.acquire() as conn:
            total_sessions = await conn.fetchval(
                'SELECT COUNT(*) FROM sessions WHERE guild_id = $1',
                ctx.guild_id
            )
            active_sessions = await conn.fetchval(
                'SELECT COUNT(*) FROM sessions WHERE guild_id = $1 AND status = $2',
                ctx.guild_id, 'active'
            )
        
        status_msg = (
            f'📊 **Bot Status**\n\n'
            f'**Sessions:**\n'
            f'• Total: {total_sessions}\n'
            f'• Active: {active_sessions}\n\n'
            f'**System:**\n'
            f'• Latency: {round(bot.latency * 1000)}ms\n'
            f'• Guilds: {len(bot.guilds)}'
        )
        
        await ctx.followup.send(status_msg)
        
    except Exception as e:
        logger.error(f'Status failed: {e}')
        await ctx.followup.send(f'Error: {str(e)}')


if __name__ == '__main__':
    # Get token with fallback
    token = os.getenv('DISCORD_TOKEN')
    
    if not token:
        logger.error('DISCORD_TOKEN not found!')
        sys.exit(1)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info('Starting Chronicle Bot...')
    
    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info('Keyboard interrupt received')
    except Exception as e:
        logger.error(f'Bot crashed: {e}', exc_info=True)
    finally:
        logger.info('Bot stopped')