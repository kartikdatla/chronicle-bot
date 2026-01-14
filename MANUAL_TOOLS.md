\# Manual Recovery Tools



Chronicle Bot includes manual recovery tools for situations where the automated `/transcribe` command fails or you need to regenerate outputs.



\## 🎯 When to Use These Tools



Use manual tools when:

\- ✅ `/transcribe` command times out or fails

\- ✅ You need to regenerate a summary with different settings

\- ✅ The Word document wasn't created properly

\- ✅ You want to test the bot installation

\- ✅ Audio files exist but transcription is missing



---



\## 🛠️ Available Tools



\### 1. `test\_installation.py` - Installation Validator



\*\*Purpose:\*\* Verify all dependencies are installed correctly before running the bot.



\*\*Usage:\*\*

```powershell

python test\_installation.py

```



\*\*What it checks:\*\*

\- ✅ Python version (3.10+)

\- ✅ Python packages (py-cord, asyncpg, whisper, etc.)

\- ✅ Node.js and npm

\- ✅ Node.js packages (docx, docx-templates)

\- ✅ PostgreSQL installation

\- ✅ Database connection

\- ✅ Ollama and llama3.2:3b model

\- ✅ Discord token in .env

\- ✅ Required files (bot/main.py, transcript\_exporter.js, etc.)



\*\*Expected Output:\*\*

```

============================================================

Chronicle Bot Installation Validator v1.1.0

============================================================



🐍 Testing Python version...

&nbsp;  ✅ Python 3.11.0



📦 Testing Python packages...

&nbsp;  ✅ py-cord

&nbsp;  ✅ asyncpg

&nbsp;  ✅ openai-whisper

&nbsp;  \[...]



✅ All tests passed! Chronicle Bot is ready to use.

```



\*\*Run this FIRST before using the bot!\*\*



---



\### 2. `manual\_transcribe.py` - Full Transcription Pipeline



\*\*Purpose:\*\* Complete transcription workflow - converts audio to text, creates Word document, and generates summary.



\*\*When to use:\*\*

\- The `/transcribe` command failed completely

\- You have audio files but no transcript

\- Starting from scratch with a session



\*\*Usage:\*\*

```powershell

python manual\_transcribe.py <session-folder-name>

```



\*\*Example:\*\*

```powershell

\# Find your session folder

ls data/audio/



\# Run transcription

python manual\_transcribe.py 01484be1-3c61-414a-b44f-6dee7809338b

```



\*\*What it does:\*\*

1\. ✅ Finds all .wav files in the session folder

2\. ✅ Registers files in database

3\. ✅ Transcribes audio using Whisper AI (with progress bar)

4\. ✅ Generates AI summary using Ollama

5\. ✅ Creates formatted Word document

6\. ✅ Saves everything to `data/transcripts/\[session-folder]/`



\*\*Progress Display:\*\*

```

🎯 Manual transcription for: 01484be1-3c61-414a-b44f-6dee7809338b

============================================================

✅ Found 5 audio files

✅ Using existing session: 01484be1



📁 Registering audio files...

Registering: 100%|██████████| 5/5 \[00:00<00:00, 124.32file/s]



🎙️ Starting transcription...

⏱️  This will take 2-4 minutes per hour of audio



Transcribing: 100%|████████| 5/5 \[15:23<00:00, 184.78s/file] ✅ User 1234



✅ Transcribed 420 segments from 5 users



📝 Generating AI summary...

✅ Summary generated (1247 words)



📄 Creating Word document...

✅ Word document created



🎉 SUCCESS!

```



\*\*Time estimate:\*\* 2-4 minutes per hour of audio



---



\### 3. `manual\_summarize.py` - Summary Generator Only



\*\*Purpose:\*\* Generate or regenerate ONLY the AI summary (transcript must already exist).



\*\*When to use:\*\*

\- Transcription succeeded but summary failed

\- You want to regenerate the summary with different settings

\- Summary quality was poor and you want to try again



\*\*Usage:\*\*

```powershell

python manual\_summarize.py <session-folder-name>

```



\*\*Example:\*\*

```powershell

python manual\_summarize.py 01484be1-3c61-414a-b44f-6dee7809338b

```



\*\*Prerequisites:\*\*

\- ⚠️ Transcripts must already exist in database

\- ⚠️ Run `manual\_transcribe.py` first if starting from scratch



\*\*What it does:\*\*

1\. ✅ Reads transcripts from database

2\. ✅ Calls Ollama AI to generate summary

3\. ✅ Saves to `data/transcripts/\[session-folder]/summary.txt`

4\. ✅ Shows preview of first 500 characters



\*\*Output:\*\*

```

🤖 Manual summary generation for: 01484be1-3c61-414a-b44f-6dee7809338b

✅ Found session: 01484be1-3c61-414a-b44f-6dee7809338b

✅ Found 5 transcripts



📝 Generating AI summary...

⏳ This may take 30-90 seconds...



✅ Summary generated (1247 words)



🎉 SUCCESS!

📝 Summary saved to: data\\transcripts\\...\\summary.txt

```



\*\*Time estimate:\*\* 30-90 seconds



---



\### 4. `manual\_create\_document.py` - Word Document Only



\*\*Purpose:\*\* Create or recreate ONLY the Word document (transcript must already exist).



\*\*When to use:\*\*

\- Transcription succeeded but Word document wasn't created

\- Document is corrupted and needs regeneration

\- You want to update the document with a new summary



\*\*Usage:\*\*

```powershell

python manual\_create\_document.py <session-folder-name>

```



\*\*Example:\*\*

```powershell

python manual\_create\_document.py 01484be1-3c61-414a-b44f-6dee7809338b

```



\*\*Prerequisites:\*\*

\- ⚠️ Transcripts must already exist in database

\- ⚠️ Run `manual\_transcribe.py` first if starting from scratch



\*\*What it does:\*\*

1\. ✅ Reads transcripts from database

2\. ✅ Reads existing summary (if available)

3\. ✅ Calls Node.js exporter to create Word document

4\. ✅ Saves to `data/transcripts/\[session-folder]/transcript.docx`



\*\*Output:\*\*

```

📄 Creating Word document for: 01484be1-3c61-414a-b44f-6dee7809338b

✅ Found session: 01484be1-3c61-414a-b44f-6dee7809338b

✅ Found 5 transcripts

✅ Participants: av0011, balo0, pikoki, spanner94, tempestevil



📝 Creating Word document...

✅ Word document created: transcript.docx

💾 File size: 45.2 KB



🎉 SUCCESS!

```



\*\*Time estimate:\*\* 5-10 seconds



---



\## 📊 Typical Workflow



\### ❌ If `/transcribe` fails completely:

```powershell

\# Step 1: Full transcription from audio files

python manual\_transcribe.py 01484be1-3c61-414a-b44f-6dee7809338b



\# Done! Everything is created.

```



\### ⚠️ If transcription worked but summary failed:

```powershell

\# Just regenerate the summary

python manual\_summarize.py 01484be1-3c61-414a-b44f-6dee7809338b



\# Then recreate document with new summary

python manual\_create\_document.py 01484be1-3c61-414a-b44f-6dee7809338b

```



\### 📄 If only the Word document is missing:

```powershell

\# Just create the document

python manual\_create\_document.py 01484be1-3c61-414a-b44f-6dee7809338b

```



---



\## 🔍 Finding Your Session Folder



\*\*Method 1: Check audio directory\*\*

```powershell

ls data/audio/

```



\*\*Method 2: Check Discord\*\*

\- Look at the session ID from `/start` or `/stop` command

\- Folder name starts with the session ID (first 8 chars)



\*\*Example:\*\*

\- Session ID from Discord: `01484be1...`

\- Folder name: `01484be1-3c61-414a-b44f-6dee7809338b`



---



\## 🐛 Troubleshooting



\### "No .wav files found"

\- ✅ Check you're using the correct session folder name

\- ✅ Audio files should be in `data/audio/\[session-folder]/`

\- ✅ Files should have .wav extension



\### "Session not found"

\- ✅ The session might not be in the database yet

\- ✅ `manual\_transcribe.py` will create it automatically

\- ✅ Other tools require the session to exist first



\### "No transcripts found"

\- ✅ Run `manual\_transcribe.py` first to create transcripts

\- ✅ `manual\_summarize.py` and `manual\_create\_document.py` need existing transcripts



\### "Node.js exporter timed out"

\- ✅ Check Node.js is installed: `node --version`

\- ✅ Check dependencies: `npm install`

\- ✅ Try running the document creator again



\### "Ollama connection failed"

\- ✅ Check Ollama is running: `ollama list`

\- ✅ Verify llama3.2:3b model: `ollama pull llama3.2:3b`

\- ✅ Summary generation requires Ollama to be running



---



\## ⚡ Quick Reference



| Tool | Speed | Purpose | Requires |

|------|-------|---------|----------|

| `test\_installation.py` | 30 sec | Validate setup | Nothing |

| `manual\_transcribe.py` | 15-30 min | Full pipeline | Audio files |

| `manual\_summarize.py` | 1-2 min | Summary only | Transcripts in DB |

| `manual\_create\_document.py` | 10 sec | Word doc only | Transcripts in DB |



---



\## 💡 Tips



1\. \*\*Always run `test\_installation.py` first\*\* on a new installation

2\. \*\*Use progress bars\*\* - don't interrupt transcription!

3\. \*\*Check audio quality\*\* before long sessions (test with 5 min recording)

4\. \*\*Keep Ollama running\*\* if you plan to use summaries

5\. \*\*Backup your data\*\* - copy `data/` folder regularly



---



\## 📞 Need Help?



If you encounter issues:



1\. \*\*Check the logs:\*\* Look at `bot.log` for detailed error messages

2\. \*\*Verify installation:\*\* Run `test\_installation.py`

3\. \*\*Check file permissions:\*\* Ensure you can write to `data/` directory

4\. \*\*Database connection:\*\* Verify PostgreSQL is running

5\. \*\*Open an issue:\*\* https://github.com/kartikdatla/chronicle-bot/issues



---



\*\*Chronicle Bot v1.1.0\*\* | Manual Tools Documentation

