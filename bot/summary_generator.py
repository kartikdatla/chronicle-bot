"""
Summary Generator - Optimized AI-powered story summaries

Uses local Ollama to generate engaging narrative summaries from transcripts
with retry logic, timeout handling, and quality validation.
"""

import ollama
import logging
import asyncio
from pathlib import Path

logger = logging.getLogger(__name__)


class SummaryGenerator:
    """
    Generates story-format summaries using local AI
    
    Features:
    - Retry logic for failed generations
    - Timeout handling
    - Quality validation
    - Fallback mechanisms
    - Scales detail with session length
    """
    
    def __init__(self, model='llama3.2:3b', output_base_dir='./data/transcripts'):
        """
        Initialize generator
        
        Args:
            model: Ollama model name
            output_base_dir: Base directory for transcript outputs
        """
        self.model = model
        self.output_base_dir = Path(output_base_dir)
        self.output_base_dir.mkdir(parents=True, exist_ok=True)
        self.max_retries = 3
        self.timeout = 120  # Increased for longer summaries
        
        logger.info(f'SummaryGenerator initialized (model={model})')
    
    async def generate_summary(self, session_id, transcript_data, session_name=None):
        """
        Generate AI summary from transcript
        
        Args:
            session_id: Session UUID
            transcript_data: List of {user_name, text} dictionaries
            session_name: Optional session name
        
        Returns:
            Path: Path to summary file
        """
        logger.info(f'🤖 Generating AI summary for session {session_id[:8]}')
        
        # Create session directory
        session_dir = self.output_base_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        
        summary_path = session_dir / 'summary.txt'
        
        # Format transcript
        transcript_text = self._format_transcript(transcript_data)
        
        # Validate transcript
        if not transcript_text or len(transcript_text) < 50:
            logger.warning('Transcript too short for meaningful summary')
            self._save_fallback_summary(
                summary_path,
                'Transcript too short to generate summary.',
                transcript_text
            )
            return summary_path
        
        # Calculate session length (estimate based on dialogue count)
        session_length = len(transcript_data)
        
        # Generate with retry
        for attempt in range(self.max_retries):
            try:
                summary = await self._generate_with_timeout(
                    transcript_text,
                    session_name,
                    session_length
                )
                
                if summary and len(summary) > 100:
                    # Save successful summary
                    summary_path.write_text(summary, encoding='utf-8')
                    
                    logger.info(
                        f'✅ AI summary generated: {len(summary)} characters, '
                        f'{len(summary.split())} words'
                    )
                    
                    return summary_path
                else:
                    logger.warning(f'Summary too short on attempt {attempt + 1}')
                    
            except asyncio.TimeoutError:
                logger.warning(f'AI generation timed out (attempt {attempt + 1}/{self.max_retries})')
            except Exception as e:
                logger.error(f'AI generation failed (attempt {attempt + 1}/{self.max_retries}): {e}')
            
            # Wait before retry
            if attempt < self.max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # All retries failed - save fallback
        logger.error('All summary generation attempts failed')
        self._save_fallback_summary(
            summary_path,
            'AI summary generation failed after multiple attempts.',
            transcript_text
        )
        
        return summary_path
    
    async def _generate_with_timeout(self, transcript_text, session_name, session_length):
        """
        Generate summary with timeout
        
        Args:
            transcript_text: Formatted transcript
            session_name: Session name
            session_length: Number of dialogue exchanges
        
        Returns:
            str: Generated summary
        """
        prompt = self._create_prompt(transcript_text, session_name, session_length)
        
        # Run in executor to avoid blocking
        loop = asyncio.get_event_loop()
        
        summary = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                self._call_ollama,
                prompt,
                session_length
            ),
            timeout=self.timeout
        )
        
        return summary
    
    def _call_ollama(self, prompt, session_length):
        """
        Synchronous Ollama call (runs in executor)
        
        Args:
            prompt: Full prompt for AI
            session_length: Number of dialogue exchanges
        
        Returns:
            str: Generated text
        """
        # Scale token count based on session length
        # Short session (<100 exchanges): 600 tokens
        # Medium session (100-300): 1000 tokens
        # Long session (300+): 1500 tokens
        if session_length < 100:
            num_predict = 600
        elif session_length < 300:
            num_predict = 1000
        else:
            num_predict = 1500
        
        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }],
                options={
                    'temperature': 0.7,
                    'top_p': 0.9,
                    'num_predict': num_predict
                }
            )
            
            return response['message']['content']
            
        except Exception as e:
            logger.error(f'Ollama API error: {e}')
            raise
    
    def _create_prompt(self, transcript_text, session_name, session_length):
        """
        Create the AI prompt for "Previously on..." style recap
        
        Args:
            transcript_text: Formatted transcript
            session_name: Session name
            session_length: Number of dialogue exchanges
        
        Returns:
            str: Complete prompt
        """
        # Determine detail level
        if session_length < 100:
            detail_instruction = "Keep it concise (3-4 paragraphs, 300-400 words)."
        elif session_length < 300:
            detail_instruction = "Provide good detail (5-7 paragraphs, 600-800 words)."
        else:
            detail_instruction = "Provide comprehensive detail (8-12 paragraphs, 1000-1500 words). Break into clear sections by major story beats."
        
        prompt = f'''You are creating a "Previously on..." style recap for a tabletop RPG session. This will be read aloud at the start of the next session.

**Session Length:** {session_length} dialogue exchanges ({"short" if session_length < 100 else "medium" if session_length < 300 else "long"} session)

**Instructions:**
START with "Previously on {session_name or "our campaign"}..."

Then cover these elements IN DETAIL (only if they appear in the transcript):

1. **CHARACTER ACTIONS**: What each player character did. Use their character names.
   - Be specific about what they accomplished
   - Include failed attempts or setbacks
   - Mention character moments and development

2. **STORY PROGRESSION**: Key plot developments and discoveries
   - Major revelations and mysteries uncovered
   - Plot threads introduced or resolved
   - Important clues or foreshadowing

3. **IMPORTANT DIALOGUE**: Brief quotes that moved the story forward
   - Use actual quotes when they're pivotal
   - Paraphrase longer conversations
   - Capture the tone and emotion

4. **CHARACTER CHANGES** (if mentioned):
   - HP/injuries: "Ragnar was badly wounded in the ambush"
   - Inventory: "The party found a mysterious amulet"
   - Currency: "They spent 200 gold on supplies"
   - Abilities: "Selene learned a new spell"
   - Relationships: New allies or enemies made

5. **COMBAT**: Major battles and outcomes
   - Who they fought and why
   - Tactics used
   - Consequences of the fight

6. **NPCs**: Important characters met or interacted with
   - Their names and roles
   - What information they provided
   - How relationships developed

7. **LOCATIONS**: Key places visited or mentioned
   - Where the party went
   - Important features of locations
   - Any map or geography details

8. **DECISIONS**: Key choices that will impact future sessions
   - What options were considered
   - What was chosen and why
   - Potential consequences

9. **FACTIONS & POLITICS**: Mentions of organizations, alliances, conflicts
   - Reputation changes
   - Political developments
   - Faction activities

10. **MYSTERIES & HOOKS**: Unresolved questions and future plot threads
    - What mysteries remain
    - What the party plans to do next
    - Cliffhangers

**Style:**
- Past tense
- Dramatic and engaging
- Focus on what matters for next session
- Use character names, not player names
- {detail_instruction}

**Format for Long Sessions:**
Break into sections with clear transitions:
- Opening scene recap
- Main story beats (2-3 sections)
- Combat/action sequences
- Character moments
- Resolution and cliffhanger

**Transcript:**
{transcript_text}

**Write the "Previously on..." recap now:**'''
        
        return prompt
    
    def _format_transcript(self, transcript_data):
        """
        Format transcript data as readable text
        
        Args:
            transcript_data: List of {user_name, text} dicts
        
        Returns:
            str: Formatted transcript
        """
        if not transcript_data:
            return ''
        
        lines = []
        for entry in transcript_data:
            speaker = entry.get('user_name', 'Unknown')
            text = entry.get('text', '').strip()
            if text:
                lines.append(f'{speaker}: {text}')
        
        return '\n\n'.join(lines)
    
    def _save_fallback_summary(self, path, reason, transcript_text):
        """
        Save fallback summary when AI generation fails
        
        Args:
            path: Output path
            reason: Reason for fallback
            transcript_text: Raw transcript
        """
        fallback_content = (
            f'AI SUMMARY GENERATION FAILED\n'
            f'{"=" * 50}\n\n'
            f'Reason: {reason}\n\n'
            f'RAW TRANSCRIPT:\n'
            f'{"=" * 50}\n\n'
            f'{transcript_text[:1000]}'
        )
        
        if len(transcript_text) > 1000:
            fallback_content += '\n\n... (transcript truncated)'
        
        path.write_text(fallback_content, encoding='utf-8')
        logger.info(f'Saved fallback summary to {path}')
    
    async def test_connection(self):
        """
        Test if Ollama is reachable
        
        Returns:
            bool: True if Ollama is available
        """
        try:
            loop = asyncio.get_event_loop()
            await asyncio.wait_for(
                loop.run_in_executor(
                    None,
                    lambda: ollama.chat(
                        model=self.model,
                        messages=[{'role': 'user', 'content': 'Hi'}]
                    )
                ),
                timeout=5
            )
            logger.info('✅ Ollama connection test successful')
            return True
        except Exception as e:
            logger.error(f'❌ Ollama connection test failed: {e}')
            return False