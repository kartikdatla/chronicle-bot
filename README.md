\# Chronicle Bot v1.1.0



🎲 Automatically record, transcribe, and summarize your Discord RPG sessions!



\## ✨ Features



\- \*\*Per-User Voice Recording\*\*: Captures each player separately for crystal-clear transcription

\- \*\*Whisper AI Transcription\*\*: Free, local, and accurate speech-to-text with timestamps

\- \*\*Timestamp Tracking\*\*: See exactly when each line was spoken `\[MM:SS]`

\- \*\*Fantasy Name Correction\*\*: Automatically fixes commonly misheard RPG terms

\- \*\*AI-Powered Summaries\*\*: Generates 300-1500 word "Previously On..." recaps

\- \*\*Word Document Exports\*\*: Professional formatting ready for sharing

\- \*\*PostgreSQL Database\*\*: Reliable session history and management



\## 🚀 Quick Start



\### Requirements



\- Python 3.10+

\- Node.js 18+

\- PostgreSQL 14+

\- Ollama (for AI summaries)

\- Discord Bot Token



\### Installation



1\. \*\*Download the latest release\*\*: \[chronicle-bot-dist-v1.1.0.zip](https://github.com/kartikdatla/chronicle-bot/releases/latest)



2\. \*\*Extract and open the Installation Guide\*\*: `Installation\_Guide\_v1.1.0.docx` contains complete step-by-step instructions



3\. \*\*Or follow these quick steps\*\*:

```bash

&nbsp;  # Setup database

&nbsp;  psql -U postgres -c "CREATE DATABASE rpg\_sessions;"

&nbsp;  psql -U postgres -d rpg\_sessions -f database/schema.sql

&nbsp;  

&nbsp;  # Install Ollama model

&nbsp;  ollama pull llama3.2:3b

&nbsp;  

&nbsp;  # Configure

&nbsp;  cp .env.example .env

&nbsp;  # Edit .env with your Discord token

&nbsp;  

&nbsp;  # Install dependencies

&nbsp;  pip install -r requirements.txt

&nbsp;  npm install

&nbsp;  

&nbsp;  # Run

&nbsp;  python bot/main.py

```



\## 🎮 Usage



1\. \*\*Start Recording\*\*: Join a voice channel and type `/start`

2\. \*\*Stop Recording\*\*: Type `/stop` when session ends

3\. \*\*Generate Transcript\*\*: Type `/transcribe` and wait 2-5 minutes

4\. \*\*Find Your Files\*\*: 

&nbsp;  - Transcripts: `data/transcripts/\[session-id]/transcript.docx`

&nbsp;  - Summaries: `data/transcripts/\[session-id]/summary.txt`



\## 📚 Documentation



\- \[Installation Guide](https://github.com/kartikdatla/chronicle-bot/releases/latest) - Complete 20+ page setup guide

\- \[CHANGELOG.md](CHANGELOG.md) - Version history and updates

\- \[Troubleshooting](#troubleshooting) - Common issues and solutions



\## 🎨 What's New in v1.1.0



\- ✅ Timestamps in transcripts `\[MM:SS]` format

\- ✅ Fantasy name auto-correction (Algonstar, Blight College, Shield Marshals, etc.)

\- ✅ Enhanced AI summaries that scale with session length (300-1500 words)

\- ✅ "Previously On..." TV-style recap format

\- ✅ Fixed duplicate participants bug

\- ✅ Fixed all timestamps showing \[0:00]

\- ✅ Improved chronological ordering



See \[CHANGELOG.md](CHANGELOG.md) for complete details.



\## 🐛 Troubleshooting



\### Bot shows offline

\- Check Command Prompt is still open

\- Verify "Bot ready!" message appeared

\- Restart: `Ctrl+C` then `python bot/main.py`



\### DISCORD\_TOKEN not found

\- Check `.env` file exists

\- Verify token is pasted correctly (no extra spaces)



\### Database connection failed

\- Ensure PostgreSQL is running

\- Verify password in `.env` matches PostgreSQL password



\### No audio found

\- Type `/start` BEFORE joining voice channel

\- Check bot has voice permissions in Discord



\### Transcription is slow

\- Normal! Expect ~3 minutes per hour of audio

\- Uses CPU transcription (not GPU)



For more help, see the Installation Guide or \[open an issue](https://github.com/kartikdatla/chronicle-bot/issues).



\## 🔒 Security



\- \*\*Never share your `.env` file\*\* - it contains your bot token

\- \*\*Regenerate token if exposed\*\* at discord.com/developers

\- \*\*Audio files contain actual voices\*\* - keep them private

\- \*\*Backup your database\*\* regularly



\## 🤝 Contributing



Found a bug? Have a feature request? \[Open an issue](https://github.com/kartikdatla/chronicle-bot/issues)!



\## 📊 Performance



\- \*\*Long Sessions\*\*: 2+ hours work fine, just take longer to process

\- \*\*Multiple Users\*\*: Handles up to 6 users comfortably

\- \*\*Disk Space\*\*: ~250 MB per hour per user

\- \*\*Summary Quality\*\*: Longer sessions get more detailed summaries



\## 💰 Cost



\*\*Completely FREE!\*\* 

\- No API costs (uses local Whisper and Ollama)

\- No subscriptions

\- Open source under MIT license



\## 📜 License



MIT License - Free to use, modify, and distribute.



See \[LICENSE](LICENSE) for details.



\## 🙏 Acknowledgments



\- \[OpenAI Whisper](https://github.com/openai/whisper) - Speech recognition

\- \[Ollama](https://ollama.ai/) - Local AI models

\- \[py-cord](https://github.com/Pycord-Development/pycord) - Discord bot framework

\- \[python-docx](https://python-docx.readthedocs.io/) - Word document generation



---



\*\*Chronicle Bot v1.1.0\*\* | Created by \[@kartikdatla](https://github.com/kartikdatla) | ⭐ Star this repo if you find it useful!

