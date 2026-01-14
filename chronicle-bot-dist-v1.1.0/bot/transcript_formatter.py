import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


class TranscriptFormatter:
    def __init__(self, output_base_dir='./data/transcripts'):
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_transcript(self, session_id, session_name, transcript_data, participants):
        session_dir = self.output_base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = session_dir / 'transcript.docx'
        
        # Remove duplicate participants and sort alphabetically
        unique_participants = sorted(list(set(participants)))
        
        export_data = {
            'session_id': session_id[:8],
            'session_name': session_name or 'Unnamed Session',
            'date': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'duration': f'{len(transcript_data)} dialogue exchanges',
            'participants': unique_participants,
            'transcript': [
                {
                    'speaker': entry.get('user_name', 'User ' + str(entry['user_id'])),
                    'text': entry['text'],
                    'timestamp': entry.get('timestamp', 0)  # Added timestamp
                }
                for entry in transcript_data
            ],
            'output_path': str(output_path)
        }
        
        try:
            result = subprocess.run(
                ['node', 'transcript_exporter.js'],
                input=json.dumps(export_data),
                text=True,
                capture_output=True,
                check=True,
                cwd=str(Path.cwd())
            )
            
            logger.info(f'Transcript exported: {output_path}')
            return output_path
            
        except subprocess.CalledProcessError as e:
            logger.error(f'Export failed: {e.stderr}')
            raise Exception(f'Export failed: {e.stderr}')