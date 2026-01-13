# Chronicle Bot - Distribution Package Builder
# Run this from your working bot directory

param(
    [string]$Version = "1.0.0",
    [string]$OutputPath = "..\chronicle-bot-dist"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Chronicle Bot Distribution Builder" -ForegroundColor Cyan
Write-Host " Version: $Version" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$DistPath = "$OutputPath-v$Version"

# Step 1: Create distribution folder
Write-Host "[1/11] Creating distribution folder..." -ForegroundColor Yellow
if (Test-Path $DistPath) {
    Write-Host "  Removing existing distribution folder..." -ForegroundColor Gray
    Remove-Item $DistPath -Recurse -Force
}
New-Item -Path $DistPath -ItemType Directory | Out-Null
Write-Host "  Created: $DistPath" -ForegroundColor Green

# Step 2: Copy bot files
Write-Host "[2/11] Copying bot source files..." -ForegroundColor Yellow
$BotFiles = @(
    "bot\main.py",
    "bot\config.py",
    "bot\session_manager.py",
    "bot\voice_manager.py",
    "bot\voice_receiver.py",
    "bot\per_user_sink.py",
    "bot\transcription_orchestrator.py",
    "bot\whisper_provider.py",
    "bot\transcript_formatter.py",
    "bot\summary_generator.py"
)

New-Item -Path "$DistPath\bot" -ItemType Directory | Out-Null
foreach ($file in $BotFiles) {
    if (Test-Path $file) {
        Copy-Item $file -Destination "$DistPath\bot\" -Force
        Write-Host "  Copied: $file" -ForegroundColor Gray
    } else {
        Write-Host "  Missing: $file" -ForegroundColor Red
    }
}

# Step 3: Create database folder and schema
Write-Host "[3/11] Creating database files..." -ForegroundColor Yellow
New-Item -Path "$DistPath\database" -ItemType Directory | Out-Null

if (Test-Path "database\schema.sql") {
    Copy-Item "database\schema.sql" -Destination "$DistPath\database\" -Force
    Write-Host "  Copied database schema" -ForegroundColor Green
} elseif (Test-Path "schema.sql") {
    Copy-Item "schema.sql" -Destination "$DistPath\database\" -Force
    Write-Host "  Copied schema.sql" -ForegroundColor Green
} else {
    Write-Host "  WARNING: schema.sql not found" -ForegroundColor Yellow
    Write-Host "  Download schema.sql and place in $DistPath\database\" -ForegroundColor Gray
}

# Step 4: Copy Node.js files
Write-Host "[4/11] Copying Node.js files..." -ForegroundColor Yellow
if (Test-Path "transcript_exporter.js") {
    Copy-Item "transcript_exporter.js" -Destination "$DistPath\" -Force
    Write-Host "  Copied transcript exporter" -ForegroundColor Green
} else {
    Write-Host "  WARNING: transcript_exporter.js not found" -ForegroundColor Red
}

# Step 5: Create data directories
Write-Host "[5/11] Creating data directories..." -ForegroundColor Yellow
New-Item -Path "$DistPath\data\audio" -ItemType Directory -Force | Out-Null
New-Item -Path "$DistPath\data\transcripts" -ItemType Directory -Force | Out-Null
New-Item -Path "$DistPath\data\audio\.gitkeep" -ItemType File -Force | Out-Null
New-Item -Path "$DistPath\data\transcripts\.gitkeep" -ItemType File -Force | Out-Null
Write-Host "  Created data directories" -ForegroundColor Green

# Step 6: Create scripts directory
Write-Host "[6/11] Creating setup scripts..." -ForegroundColor Yellow
New-Item -Path "$DistPath\scripts" -ItemType Directory | Out-Null

$SetupBat = @'
@echo off
echo ==========================================
echo  Chronicle Bot - Windows Setup
echo ==========================================
echo.

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Install Python 3.11+
    pause
    exit /b 1
)

echo [2/5] Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found! Install Node.js 18+
    pause
    exit /b 1
)

echo [3/5] Installing Python dependencies...
pip install -r requirements.txt

echo [4/5] Installing Node.js dependencies...
npm install

echo [5/5] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created! Edit with your token.
) else (
    echo .env file exists, skipping...
)

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env with your Discord token
echo 2. Create database: psql -U postgres -c "CREATE DATABASE rpg_sessions;"
echo 3. Run schema: psql -U postgres -d rpg_sessions -f database\schema.sql
echo 4. Start Ollama: ollama serve
echo 5. Pull AI model: ollama pull llama3.2:3b
echo 6. Start bot: python bot\main.py
echo.
pause
'@

$SetupBat | Out-File -FilePath "$DistPath\scripts\setup.bat" -Encoding ASCII
Write-Host "  Created Windows setup script" -ForegroundColor Green

# Step 7: Create .env.example
Write-Host "[7/11] Creating .env.example..." -ForegroundColor Yellow
@"
DISCORD_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/rpg_sessions
OLLAMA_MODEL=llama3.2:3b
WHISPER_MODEL=base
ENABLE_AI_SUMMARY=true
LOG_LEVEL=INFO
"@ | Out-File -FilePath "$DistPath\.env.example" -Encoding UTF8
Write-Host "  Created .env.example" -ForegroundColor Green

# Step 8: Create requirements.txt
Write-Host "[8/11] Creating requirements.txt..." -ForegroundColor Yellow
@"
py-cord[voice]==2.7.0
asyncpg==0.29.0
openai-whisper==20231117
ollama==0.4.7
python-dotenv==1.0.0
psutil==5.9.8
wave==0.0.2
"@ | Out-File -FilePath "$DistPath\requirements.txt" -Encoding UTF8
Write-Host "  Created requirements.txt" -ForegroundColor Green

# Step 9: Create package.json
Write-Host "[9/11] Creating package.json..." -ForegroundColor Yellow
@"
{
  "name": "chronicle-bot",
  "version": "$Version",
  "description": "Discord RPG session recorder",
  "main": "transcript_exporter.js",
  "dependencies": {
    "docx": "^8.5.0"
  }
}
"@ | Out-File -FilePath "$DistPath\package.json" -Encoding UTF8
Write-Host "  Created package.json" -ForegroundColor Green

# Step 10: Create README.md
Write-Host "[10/11] Creating README.md..." -ForegroundColor Yellow
@"
# Chronicle Bot v$Version

Record, transcribe, and summarize your RPG sessions with AI!

## Quick Start

1. Install Python 3.11+, Node.js 18+, PostgreSQL 14+, Ollama
2. Run: scripts\setup.bat (Windows)
3. Edit .env with your Discord token
4. Start: python bot\main.py

## Features

- Real-time voice recording
- AI transcription with Whisper
- Story summaries with Ollama
- Professional Word documents
- Chronological conversation ordering

## Commands

- /start - Start recording
- /stop - Stop recording
- /transcribe - Generate transcript
- /status - Check bot status

## Documentation

See docs/ folder for complete guides.

## License

See LICENSE file
"@ | Out-File -FilePath "$DistPath\README.md" -Encoding UTF8
Write-Host "  Created README.md" -ForegroundColor Green

# Step 11: Create docs folder
Write-Host "[11/11] Creating docs folder..." -ForegroundColor Yellow
New-Item -Path "$DistPath\docs" -ItemType Directory | Out-Null
@"
# Documentation

Add these files before distribution:
- INSTALLATION_GUIDE.md
- LICENSE
- LICENSING_GUIDE.md (optional)
"@ | Out-File -FilePath "$DistPath\docs\README.md" -Encoding UTF8
Write-Host "  Created docs folder" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Distribution Created Successfully!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Location: $DistPath" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Copy docs to $DistPath\docs\" -ForegroundColor White
Write-Host "2. Add LICENSE file" -ForegroundColor White
Write-Host "3. Test on clean system" -ForegroundColor White
Write-Host "4. Create ZIP:" -ForegroundColor White
Write-Host "   Compress-Archive -Path '$DistPath\*' -DestinationPath 'chronicle-bot-v$Version.zip'" -ForegroundColor Gray
Write-Host ""
