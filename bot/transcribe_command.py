"""
Updated /transcribe command for main.py

Replace the transcribe_cmd function in your main.py with this version
"""

@bot.slash_command(
    name='transcribe',
    description='Transcribe and summarize last session'
)
async def transcribe_cmd(ctx: discord.ApplicationContext):
    """Generate chronologically-ordered transcript and AI summary"""
    if not transcription_orchestrator:
        await ctx.respond('Bot initializing...', ephemeral=True)
        return
    
    await ctx.defer()
    
    try:
        # Get most recent completed session
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
            f'⏳ Step 1/3: Transcribing audio with timestamps...'
        )
        
        # Transcribe - returns chronologically ordered segments
        segments = await transcription_orchestrator.transcribe_session(session_id)
        
        if not segments:
            await progress_msg.edit(content='No audio found.')
            return
        
        # Count unique participants
        unique_users = set(seg['user_id'] for seg in segments)
        
        await progress_msg.edit(
            content=f'🔄 **Processing Session**\n'
                    f'✅ Step 1/3: Transcribed {len(unique_users)} participants '
                    f'({len(segments)} dialogue segments)\n'
                    f'⏳ Step 2/3: Generating chronological transcript...'
        )
        
        # Prepare chronologically-ordered transcript data
        transcript_data = []
        participants = []
        user_names = {}
        
        for seg in segments:
            user_id = seg['user_id']
            
            # Get user name (cache it)
            if user_id not in user_names:
                member = ctx.guild.get_member(user_id)
                user_name = member.name if member else f"User {user_id}"
                user_names[user_id] = user_name
                if user_name not in participants:
                    participants.append(user_name)
            else:
                user_name = user_names[user_id]
            
            transcript_data.append({
                'user_id': user_id,
                'user_name': user_name,
                'text': seg['text'],
                'timestamp': seg['timestamp']
            })
        
        # Export chronological transcript
        transcript_path = await transcript_formatter.export_transcript(
            session_id,
            session_name,
            transcript_data,
            participants
        )
        
        await progress_msg.edit(
            content=f'🔄 **Processing Session**\n'
                    f'✅ Step 1/3: Transcribed {len(unique_users)} participants\n'
                    f'✅ Step 2/3: Chronological transcript created\n'
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
        
        # Show preview (first 3 exchanges)
        preview_segments = transcript_data[:3]
        preview = '\n'.join([
            f'**{t["user_name"]}:** {t["text"][:80]}{"..." if len(t["text"]) > 80 else ""}'
            for t in preview_segments
        ])
        
        result_message = (
            f'✅ **Processing Complete!**\n\n'
            f'📊 **Stats:**\n'
            f'• Participants: {len(participants)}\n'
            f'• Dialogue exchanges: {len(segments)}\n'
            f'• Order: Chronological ⏱️\n\n'
            f'**Preview:**\n'
            f'{preview}\n\n'
            f'📄 **Transcript:** `{transcript_path}`\n'
        )
        
        if summary_path:
            result_message += f'📖 **Summary:** `{summary_path}`\n'
        
        result_message += f'\n💾 Files: `data/transcripts/{session_id[:8]}...`'
        
        await progress_msg.edit(content=result_message)
        
        logger.info(f'Transcribed session {session_id[:8]} with {len(segments)} segments')
        
    except Exception as e:
        logger.error(f'Transcription failed: {e}', exc_info=True)
        await ctx.channel.send(f'❌ **Transcription Failed**\nError: ```{str(e)}```')
