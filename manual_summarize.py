"""
Manual summary generator for Chronicle Bot
Use when you have a transcript but need to generate/regenerate the summary
"""

import asyncio
import asyncpg
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

# Add bot directory to path
sys.path.insert(0, str(Path(__file__).parent / 'bot'))

from summary_generator import SummaryGenerator

load_dotenv()

async def manual_summarize(session_folder):
    """Manually generate summary for a session that's already transcribed"""
    
    print(f"🤖 Manual summary generation for: {session_folder}")
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL')
    db_pool = await asyncpg.create_pool(db_url)
    
    try:
        # Find session ID (first 8 chars of folder name)
        session_id = session_folder[:8]
        
        # Check if session exists and get transcript data
        async with db_pool.acquire() as conn:
            session = await conn.fetchrow(
                'SELECT id FROM sessions WHERE id::text LIKE $1',
                f'{session_id}%'
            )
            
            if not session:
                print(f"❌ Session not found: {session_id}")
                return
            
            session_id = str(session['id'])
            
            # Get all transcripts for this session
            transcripts = await conn.fetch('''
                SELECT tj.transcript_text, af.user_id
                FROM transcription_jobs tj
                JOIN audio_files af ON tj.audio_file_id = af.id
                WHERE tj.session_id = $1
                ORDER BY af.created_at
            ''', session_id)
            
            if not transcripts:
                print(f"❌ No transcripts found for session {session_id}")
                print(f"💡 Run transcription first: python manual_transcribe.py {session_folder}")
                return
            
            print(f"✅ Found session: {session_id}")
            print(f"✅ Found {len(transcripts)} transcripts")
        
        # Combine all transcripts into dialogue format
        transcript_data = []
        for t in transcripts:
            transcript_data.append({
                'speaker': f"User {t['user_id']}",
                'text': t['transcript_text']
            })
        
        # Setup output directory
        output_dir = Path('data/transcripts') / session_folder
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print("\n📝 Generating AI summary...")
        print("⏳ This may take 30-90 seconds...")
        
        # Initialize summarizer
        summarizer = SummaryGenerator('llama3.2:3b', str(output_dir))
        
        # Generate summary with transcript data
        summary_path = await summarizer.generate_summary(session_id, transcript_data)
        
        # Read the summary that was saved
        if isinstance(summary_path, Path):
            summary_file = Path(summary_path)
        elif isinstance(summary_path, str):
            summary_file = Path(summary_path)
        else:
            summary_file = output_dir / 'summary.txt'
        
        if not summary_file.exists():
            print("❌ Summary file not found")
            return
        
        summary = summary_file.read_text(encoding='utf-8')
        
        if not summary or len(summary.strip()) < 50:
            print("❌ Summary generation failed or returned empty result")
            return
        
        word_count = len(summary.split())
        print(f"✅ Summary generated ({word_count} words)")
        print(f"✅ Summary saved to: {summary_file}")
        
        print(f"\n--- PREVIEW (first 500 chars) ---")
        print(summary[:500] + "..." if len(summary) > 500 else summary)
        print("--- END PREVIEW ---")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await db_pool.close()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python manual_summarize.py <session-folder-name>")
        print("\nExample: python manual_summarize.py 01484be1-3c61-414a-b44f-6dee7809338b")
        print("\nThis generates a summary for a session that's already been transcribed.")
        print("\nTo find your session folder:")
        print("  ls data/audio/")
        print("\nNote: Run manual_transcribe.py first if you haven't transcribed yet!")
        sys.exit(1)
    
    session_folder = sys.argv[1]
    asyncio.run(manual_summarize(session_folder))