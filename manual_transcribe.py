"""
Manual transcription script for Chronicle Bot
Use when /transcribe command fails
"""

import asyncio
import asyncpg
import sys
from pathlib import Path
from dotenv import load_dotenv
import os
from tqdm import tqdm

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

from transcription_orchestrator import TranscriptionOrchestrator
from transcript_formatter import TranscriptFormatter
from summary_generator import SummaryGenerator

load_dotenv()

# Global progress bar
pbar = None

async def progress_callback(current, total, user_id, status):
    """Update the progress bar"""
    global pbar
    
    if pbar is None:
        pbar = tqdm(total=total, desc="Transcribing", unit="file", 
                   bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
    
    pbar.update(1)
    
    status_emoji = {
        'transcribing': '⏳',
        'completed': '✅',
        'failed': '❌',
        'empty': '⚠️'
    }.get(status, '⏳')
    
    pbar.set_postfix_str(f"{status_emoji} User {user_id}")

async def manual_transcribe(session_folder):
    """Manually transcribe a session folder"""
    global pbar
    
    print(f"🎯 Manual transcription for: {session_folder}")
    print("=" * 60)
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL')
    db_pool = await asyncpg.create_pool(db_url)
    
    try:
        # Initialize components
        orchestrator = TranscriptionOrchestrator(db_pool)
        formatter = TranscriptFormatter()
        
        # Get all .wav files in the folder
        audio_dir = Path('data/audio') / session_folder
        wav_files = list(audio_dir.glob('*.wav'))
        
        if not wav_files:
            print(f"❌ No .wav files found in {audio_dir}")
            return
        
        print(f"✅ Found {len(wav_files)} audio files")
        
        # Create a temporary session in database
        async with db_pool.acquire() as conn:
            # Check if session exists
            session = await conn.fetchrow(
                'SELECT id, name FROM sessions WHERE id::text LIKE $1',
                f'{session_folder[:8]}%'
            )
            
            if not session:
                # Create session
                session_id = await conn.fetchval('''
                    INSERT INTO sessions (id, guild_id, name, status, created_at)
                    VALUES ($1, $2, $3, $4, NOW())
                    RETURNING id
                ''', session_folder[:8], 0, 'Manual Transcription', 'completed')
                session_name = 'Manual Transcription'
                print(f"✅ Created session: {session_id}")
            else:
                session_id = str(session['id'])
                session_name = session['name'] or 'Manual Transcription'
                print(f"✅ Using existing session: {session_id}")
            
            # Add audio files to database
            print("\n📁 Registering audio files...")
            user_map = {}
            for wav_file in tqdm(wav_files, desc="Registering", unit="file"):
                username = wav_file.stem.rsplit('_', 2)[0]
                duration = wav_file.stat().st_size / 192000  # Approximate
                
                # Get or create user
                user_id = hash(username) % (2**31)  # Generate consistent ID
                user_map[user_id] = username
                
                file_exists = await conn.fetchval(
                    'SELECT id FROM audio_files WHERE session_id = $1 AND user_id = $2',
                    session_id, user_id
                )
                
                if not file_exists:
                    await conn.execute('''
                        INSERT INTO audio_files (session_id, user_id, file_path, duration, created_at)
                        VALUES ($1, $2, $3, $4, NOW())
                    ''', session_id, user_id, str(wav_file), duration)
        
        print("\n🎙️ Starting transcription...")
        print("⏱️  This will take 2-4 minutes per hour of audio")
        print()
        
        # Set progress callback
        orchestrator.progress_callback = progress_callback
        
        # Transcribe
        segments = await orchestrator.transcribe_session(session_id)
        
        # Close progress bar
        if pbar:
            pbar.close()
        
        if not segments:
            print("\n❌ Transcription failed - no segments generated")
            return
        
        unique_users = len(set(seg['user_id'] for seg in segments))
        print(f"\n✅ Transcribed {len(segments)} segments from {unique_users} users")
        
        # Prepare transcript data for formatter
        print("\n📄 Formatting transcript data...")
        transcript_data = []
        participants = []
        
        for seg in segments:
            user_id = seg['user_id']
            username = user_map.get(user_id, f"User {user_id}")
            
            transcript_data.append({
                'user_id': user_id,
                'user_name': username,
                'text': seg['text'],
                'timestamp': seg.get('timestamp', 0)
            })
            
            if username not in participants:
                participants.append(username)
        
        print(f"✅ Participants: {', '.join(sorted(participants))}")
        
        # Create Word document using TranscriptFormatter
        print("\n📝 Creating Word document...")
        output_dir = Path('data/transcripts') / session_folder
        output_dir.mkdir(parents=True, exist_ok=True)
        
        docx_path = await formatter.export_transcript(
            session_id,
            session_name,
            transcript_data,
            participants
        )
        
        print(f"✅ Word document created: {docx_path}")
        
        # Generate summary
        print("\n📝 Generating AI summary...")
        
        # Get transcript data for summary
        async with db_pool.acquire() as conn:
            transcripts = await conn.fetch('''
                SELECT tj.transcript_text, af.user_id
                FROM transcription_jobs tj
                JOIN audio_files af ON tj.audio_file_id = af.id
                WHERE tj.session_id = $1
                ORDER BY af.created_at
            ''', session_id)
        
        transcript_for_summary = [{
            'speaker': user_map.get(t['user_id'], f"User {t['user_id']}"),
            'text': t['transcript_text']
        } for t in transcripts]
        
        # Initialize summarizer
        summarizer = SummaryGenerator('llama3.2:3b', str(output_dir))
        
        # Generate with progress indicator
        print("🤖 Calling Ollama AI...")
        summary_path = await summarizer.generate_summary(session_id, transcript_for_summary)
        
        # Read summary
        if isinstance(summary_path, (str, Path)):
            summary_file = Path(summary_path)
            if summary_file.exists():
                summary = summary_file.read_text(encoding='utf-8')
                print(f"✅ Summary generated ({len(summary.split())} words)")
            else:
                print("⚠️  Summary file not found")
        else:
            print("⚠️  Summary generation returned unexpected result")
        
        print(f"\n{'=' * 60}")
        print(f"🎉 SUCCESS!")
        print(f"{'=' * 60}")
        print(f"📄 Transcript: {docx_path}")
        print(f"📝 Summary: {output_dir / 'summary.txt'}")
        print(f"\n💡 Files saved to: {output_dir}")
        
    except Exception as e:
        if pbar:
            pbar.close()
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_pool.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python manual_transcribe.py <session-folder-name>")
        print("\nExample: python manual_transcribe.py 01484be1-3c61-414a-b44f-6dee7809338b")
        print("\nTo find your session folder:")
        print("  ls data/audio/")
        sys.exit(1)
    
    session_folder = sys.argv[1]
    asyncio.run(manual_transcribe(session_folder))