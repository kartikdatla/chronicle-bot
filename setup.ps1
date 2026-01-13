# RPG Transcription Bot - Windows Setup Script
# Run with: .\setup.ps1

Write-Host "🎮 RPG Transcription Bot - Setup Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Helper functions
function Print-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Yellow
}

# Check prerequisites
Write-Host "Checking prerequisites..."

# Python 3.11+
$pythonVersion = $null
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python 3\.1[1-9]") {
        Print-Success "Python found: $pythonVersion"
        $PYTHON_CMD = "python"
    } else {
        Print-Error "Python 3.11+ required (found: $pythonVersion)"
        Print-Info "Download from: https://www.python.org/downloads/"
        exit 1
    }
} catch {
    Print-Error "Python not found!"
    Print-Info "Install from: https://www.python.org/downloads/"
    exit 1
}

# PostgreSQL
try {
    $null = Get-Command psql -ErrorAction Stop
    Print-Success "PostgreSQL found"
} catch {
    Print-Error "PostgreSQL not found!"
    Print-Info "Download from: https://www.postgresql.org/download/windows/"
    Print-Info "Or use: winget install PostgreSQL.PostgreSQL"
    exit 1
}

# FFmpeg
try {
    $null = Get-Command ffmpeg -ErrorAction Stop
    Print-Success "FFmpeg found"
} catch {
    Print-Error "FFmpeg not found!"
    Print-Info "Install with: winget install FFmpeg"
    exit 1
}

# Git
try {
    $null = Get-Command git -ErrorAction Stop
    Print-Success "Git found"
} catch {
    Print-Error "Git not found!"
    Print-Info "Install with: winget install Git.Git"
    exit 1
}

Write-Host ""
Write-Host "All prerequisites satisfied!" -ForegroundColor Green
Write-Host ""

# Create project structure
Write-Host "Creating project structure..."

# Create directories
New-Item -ItemType Directory -Force -Path "bot" | Out-Null
New-Item -ItemType Directory -Force -Path "stt" | Out-Null
New-Item -ItemType Directory -Force -Path "whisper" | Out-Null
New-Item -ItemType Directory -Force -Path "tests\unit" | Out-Null
New-Item -ItemType Directory -Force -Path "tests\integration" | Out-Null
New-Item -ItemType Directory -Force -Path "data\audio" | Out-Null

# Create Python package files
New-Item -ItemType File -Force -Path "bot\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "stt\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "whisper\__init__.py" | Out-Null
New-Item -ItemType File -Force -Path "tests\__init__.py" | Out-Null

Print-Success "Created directories"

# Create .gitignore
@"
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/

# Environment
.env
.env.local

# Audio files
data/audio/*
!data/audio/.gitkeep

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp

# Logs
*.log
bot.log

# OS
.DS_Store
Thumbs.db
"@ | Out-File -FilePath ".gitignore" -Encoding UTF8

Print-Success "Created .gitignore"

# Create requirements.txt
@"
# Core Discord (Phase 1)
discord.py[voice]==2.3.2
PyNaCl==1.5.0

# Database
asyncpg==0.29.0

# Environment
python-dotenv==1.0.0

# Audio (will add more in Phase 2)
wave==0.0.2
"@ | Out-File -FilePath "requirements.txt" -Encoding UTF8

Print-Success "Created requirements.txt"

# Create database schema
@"
-- RPG Transcription Bot Database Schema

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY,
    guild_id BIGINT NOT NULL,
    channel_id BIGINT NOT NULL,
    creator_id BIGINT NOT NULL,
    name TEXT,
    status VARCHAR(20) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sessions_guild ON sessions(guild_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status);

-- Participants table
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    joined_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(session_id, discord_user_id)
);

-- Audio files table
CREATE TABLE IF NOT EXISTS audio_files (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
    discord_user_id BIGINT NOT NULL,
    file_path TEXT NOT NULL,
    duration_seconds FLOAT,
    size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audio_files_session ON audio_files(session_id);
"@ | Out-File -FilePath "schema.sql" -Encoding UTF8

Print-Success "Created schema.sql"

# Create .env.example
@"
# Discord Configuration
DISCORD_TOKEN=your_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/rpg_sessions

# Storage Configuration
AUDIO_STORAGE_PATH=./data/audio

# Transcription (Phase 3+)
# STT_ASSEMBLYAI_KEYS=key1,key2
# STT_DEEPGRAM_KEYS=key1,key2
# STT_WHISPER_LOCAL_ENABLED=true
"@ | Out-File -FilePath ".env.example" -Encoding UTF8

Print-Success "Created .env.example"

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..."

if (Test-Path "venv") {
    Print-Info "Virtual environment already exists, skipping..."
} else {
    & $PYTHON_CMD -m venv venv
    Print-Success "Virtual environment created"
}

# Activate virtual environment
Print-Info "Activating virtual environment..."
& .\venv\Scripts\Activate.ps1

# Install dependencies
Write-Host ""
Write-Host "Installing Python dependencies..."
& pip install --upgrade pip --quiet
& pip install -r requirements.txt --quiet

Print-Success "Dependencies installed"

# Database setup
Write-Host ""
Write-Host "Setting up database..."

$DB_USER = Read-Host "PostgreSQL username (default: postgres)"
if ([string]::IsNullOrWhiteSpace($DB_USER)) { $DB_USER = "postgres" }

$DB_PASS = Read-Host "PostgreSQL password" -AsSecureString
$DB_PASS_Plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($DB_PASS)
)

$DB_NAME = Read-Host "Database name (default: rpg_sessions)"
if ([string]::IsNullOrWhiteSpace($DB_NAME)) { $DB_NAME = "rpg_sessions" }

# Set password for psql
$env:PGPASSWORD = $DB_PASS_Plain

# Create database
Print-Info "Creating database..."
try {
    & createdb -U $DB_USER $DB_NAME 2>$null
    Print-Success "Database created"
} catch {
    Print-Info "Database already exists"
}

# Run schema
Print-Info "Running schema..."
& psql -U $DB_USER -d $DB_NAME -f schema.sql | Out-Null
Print-Success "Schema applied"

# Create .env file
Write-Host ""
Print-Info "Creating .env file..."

$DISCORD_TOKEN = Read-Host "Discord Bot Token"

@"
# Discord Configuration
DISCORD_TOKEN=$DISCORD_TOKEN

# Database Configuration
DATABASE_URL=postgresql://$($DB_USER):$($DB_PASS_Plain)@localhost:5432/$DB_NAME

# Storage Configuration
AUDIO_STORAGE_PATH=./data/audio
"@ | Out-File -FilePath ".env" -Encoding UTF8

Print-Success ".env file created"

# Create gitkeep for audio directory
New-Item -ItemType File -Force -Path "data\audio\.gitkeep" | Out-Null

# Create minimal bot
@"
"""
Discord RPG Transcription Bot - Phase 1
Minimal bot to test connection and voice
"""

import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    logger.info(f'Bot connected as {bot.user}')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    # Sync slash commands
    await bot.tree.sync()
    logger.info('Slash commands synced')

@bot.tree.command(name="ping", description="Test if bot is alive")
async def ping(interaction: discord.Interaction):
    '''Simple test command'''
    await interaction.response.send_message(
        f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms"
    )

@bot.tree.command(name="join", description="Join your voice channel")
async def join_voice(interaction: discord.Interaction):
    '''Test voice connection'''
    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ You need to be in a voice channel!", 
            ephemeral=True
        )
        return
    
    channel = interaction.user.voice.channel
    
    try:
        await channel.connect()
        await interaction.response.send_message(f"✅ Joined {channel.name}")
    except Exception as e:
        await interaction.response.send_message(
            f"❌ Error: {e}", 
            ephemeral=True
        )
        logger.error(f"Failed to join voice: {e}")

@bot.tree.command(name="leave", description="Leave voice channel")
async def leave_voice(interaction: discord.Interaction):
    '''Disconnect from voice'''
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        await interaction.response.send_message("👋 Left voice channel")
    else:
        await interaction.response.send_message(
            "❌ Not in a voice channel", 
            ephemeral=True
        )

# Run bot
if __name__ == '__main__':
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        logger.error("DISCORD_TOKEN not found in .env file!")
        exit(1)
    
    logger.info("Starting bot...")
    bot.run(token)
"@ | Out-File -FilePath "bot\main.py" -Encoding UTF8

Print-Success "Created bot\main.py"

# Create README
@"
# RPG Transcription Bot

Discord bot for recording and transcribing tabletop RPG sessions.

## Quick Start

1. Activate virtual environment:
``````powershell
.\venv\Scripts\Activate.ps1
``````

2. Run the bot:
``````powershell
python bot\main.py
``````

3. Test in Discord:
- ``/ping`` - Test bot connection
- ``/join`` - Join your voice channel
- ``/leave`` - Leave voice channel

## Project Status

- ✅ Phase 1: Basic bot + voice connection
- ⏳ Phase 2: Audio recording (in progress)
- ⏳ Phase 3: Transcription (planned)

## Documentation

See BUILD_GUIDE_PHASE_1.md for detailed instructions.

## Troubleshooting

If bot won't start:
1. Check .env file has your Discord token
2. Make sure venv is activated
3. Check PostgreSQL is running: ``pg_isready``

For more help, see the build guides.
"@ | Out-File -FilePath "README.md" -Encoding UTF8

Print-Success "Created README.md"

# Initialize git
if (Test-Path ".git") {
    Print-Info "Git repository already initialized"
} else {
    & git init | Out-Null
    Print-Success "Git repository initialized"
}

# Final summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✓ Setup Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Project structure created:"
Write-Host "  📁 bot\           - Bot code"
Write-Host "  📁 stt\           - Transcription (Phase 3+)"
Write-Host "  📁 whisper\       - Local Whisper (Phase 3+)"
Write-Host "  📁 tests\         - Test files"
Write-Host "  📁 data\audio\    - Audio storage"
Write-Host ""
Write-Host "Database 'rpg_sessions' created and schema applied"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Activate virtual environment:" -ForegroundColor Yellow
Write-Host "     .\venv\Scripts\Activate.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "  2. Run the bot:" -ForegroundColor Yellow
Write-Host "     python bot\main.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Test in Discord:" -ForegroundColor Yellow
Write-Host "     /ping - Test connection"
Write-Host "     /join - Join voice channel"
Write-Host ""
Write-Host "For detailed instructions, see BUILD_GUIDE_PHASE_1.md"
Write-Host ""
Write-Host "Happy coding! 🎮"
