"""
Manual Word document creator for Chronicle Bot
Creates transcript.docx from database transcripts
"""

import asyncio
import asyncpg
import sys
from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

async def create_document(session_folder):
    """Create Word document from existing database transcripts"""
    
    print(f"📄 Creating Word document for: {session_folder}")
    
    # Connect to database
    db_url = os.getenv('DATABASE_URL')
    db_pool = await asyncpg.create_pool(db_url)
    
    try:
        # Find session ID
        session_id = session_folder[:8]
        
        async with db_pool.acquire() as conn:
            session = await conn.fetchrow(
                'SELECT id FROM sessions WHERE id::text LIKE $1',
                f'{session_id}%'
            )
            
            if not session:
                print(f"❌ Session not found: {session_id}")
                return
            
            session_id = str(session['id'])
            print(f"✅ Found session: {session_id}")
            
            # Get transcripts with user info
            transcripts = await conn.fetch('''
                SELECT tj.transcript_text, af.user_id, af.file_path
                FROM transcription_jobs tj
                JOIN audio_files af ON tj.audio_file_id = af.id
                WHERE tj.session_id = $1
                ORDER BY af.created_at
            ''', session_id)
            
            if not transcripts:
                print(f"❌ No transcripts found")
                return
            
            print(f"✅ Found {len(transcripts)} transcripts")
        
        # Get usernames from file paths
        user_map = {}
        for t in transcripts:
            file_path = Path(t['file_path'])
            if file_path.exists():
                username = file_path.stem.rsplit('_', 2)[0]
                user_map[t['user_id']] = username
            else:
                user_map[t['user_id']] = f"User {t['user_id']}"
        
        # Format transcript data
        transcript_data = []
        for t in transcripts:
            transcript_data.append({
                'user_id': t['user_id'],
                'user_name': user_map.get(t['user_id'], f"User {t['user_id']}"),
                'text': t['transcript_text'],
                'timestamp': 0
            })
        
        print(f"✅ Participants: {', '.join(sorted(set(user_map.values())))}")
        
        # Check for existing summary
        output_dir = Path('data/transcripts') / session_folder
        output_dir.mkdir(parents=True, exist_ok=True)
        
        summary_file = output_dir / 'summary.txt'
        if summary_file.exists():
            summary = summary_file.read_text(encoding='utf-8')
            print(f"✅ Found existing summary ({len(summary.split())} words)")
        else:
            summary = "No summary available. Run manual_summarize.py to generate one."
            print("⚠️  No summary found - using placeholder")
        
        # Create Word document using Node.js exporter
        print("\n📝 Creating Word document...")
        
        import json
        import subprocess
        
        # Prepare export data
        export_data = {
            'sessionId': session_id,
            'participants': sorted(list(set(user_map.values()))),
            'transcript': [
                {
                    'speaker': entry['user_name'].upper(),
                    'text': entry['text'],
                    'timestamp': entry.get('timestamp', 0)
                }
                for entry in transcript_data
            ],
            'summary': summary
        }
        
        # Save temp JSON
        temp_json = output_dir / 'temp_export.json'
        print(f"💾 Saving temp file: {temp_json}")
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"📊 Data prepared: {len(transcript_data)} transcript entries")
        
        # Call Node.js exporter
        docx_path = output_dir / 'transcript.docx'
        
        # Check if Node.js script exists
        exporter_script = Path('transcript_exporter.js')
        if not exporter_script.exists():
            print(f"❌ transcript_exporter.js not found in {Path.cwd()}")
            print(f"   Looking for: {exporter_script.absolute()}")
            return
        
        print(f"🟢 Calling Node.js exporter...")
        print(f"   Command: node transcript_exporter.js {temp_json} {docx_path}")
        
        result = subprocess.run(
            ['node', 'transcript_exporter.js', str(temp_json), str(docx_path)],
            capture_output=True,
            text=True,
            cwd=str(Path.cwd()),
            timeout=30
        )
        
        print(f"\n📊 Node.js result:")
        print(f"   Return code: {result.returncode}")
        
        if result.stdout:
            print(f"   Stdout: {result.stdout}")
        if result.stderr:
            print(f"   Stderr: {result.stderr}")
        
        if result.returncode == 0:
            if temp_json.exists():
                temp_json.unlink()
            
            if docx_path.exists():
                print(f"\n🎉 SUCCESS!")
                print(f"📄 Word document: {docx_path}")
                print(f"💾 File size: {docx_path.stat().st_size / 1024:.1f} KB")
            else:
                print(f"\n⚠️  Node.js exited successfully but no file created")
                print(f"   Expected: {docx_path}")
        else:
            print(f"\n❌ Export failed with code {result.returncode}")
            if temp_json.exists():
                print(f"   Debug: temp JSON still exists at {temp_json}")
        
        print(f"\n💡 Tip: Open the document to view your full transcript!")
        
    except subprocess.TimeoutExpired:
        print(f"\n❌ Node.js exporter timed out after 30 seconds")
    except FileNotFoundError as e:
        print(f"\n❌ File not found: {e}")
        print(f"   Make sure Node.js is installed: node --version")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Properly close the pool
        try:
            await asyncio.wait_for(db_pool.close(), timeout=5.0)
        except asyncio.TimeoutError:
            print("⚠️  Database pool close timed out")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python manual_create_document.py <session-folder-name>")
        print("\nExample: python manual_create_document.py 01484be1-3c61-414a-b44f-6dee7809338b")
        print("\nThis creates a Word document from database transcripts.")
        sys.exit(1)
    
    session_folder = sys.argv[1]
    
    try:
        asyncio.run(create_document(session_folder))
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)