# Chronicle Bot - Distribution Package Builder
# Run this from your working bot directory to create a clean distribution package

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
Write-Host "  ✓ Created: $DistPath" -ForegroundColor Green

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
        Write-Host "  ✓ Copied: $file" -ForegroundColor Gray
    } else {
        Write-Host "  ⚠ Missing: $file" -ForegroundColor Red
    }
}

# Step 3: Create database folder and schema
Write-Host "[3/11] Creating database files..." -ForegroundColor Yellow
New-Item -Path "$DistPath\database" -ItemType Directory | Out-Null

# Check if schema.sql exists, if not create it
if (Test-Path "schema.sql") {
    Copy-Item "schema.sql" -Destination "$DistPath\database\" -Force
    Write-Host "  ✓ Copied existing schema.sql" -ForegroundColor Green
} else {
    Write-Host "  ⚠ schema.sql not found, you'll need to add it manually" -ForegroundColor Yellow
    Write-Host "    Download schema.sql and place it in $DistPath\database\" -ForegroundColor Gray
}

# Step 4: Copy Node.js files
Write-Host "[4/11] Copying Node.js files..." -ForegroundColor Yellow
if (Test-Path "transcript_exporter.js") {
    Copy-Item "transcript_exporter.js" -Destination "$DistPath\" -Force
    Write-Host "  ✓ Copied transcript exporter" -ForegroundColor Green
} else {
    Write-Host "  ⚠ transcript_exporter.js not found" -ForegroundColor Red
}

# Step 5: Create data directories
Write-Host "[5/11] Creating data directories..." -ForegroundColor Yellow
New-Item -Path "$DistPath\data\audio" -ItemType Directory -Force | Out-Null
New-Item -Path "$DistPath\data\transcripts" -ItemType Directory -Force | Out-Null
New-Item -Path "$DistPath\data\audio\.gitkeep" -ItemType File -Force | Out-Null
New-Item -Path "$DistPath\data\transcripts\.gitkeep" -ItemType File -Force | Out-Null
Write-Host "  ✓ Created data directories" -ForegroundColor Green

# Step 6: Create scripts directory with setup scripts
Write-Host "[6/11] Creating setup scripts..." -ForegroundColor Yellow
New-Item -Path "$DistPath\scripts" -ItemType Directory | Out-Null

# Windows setup script
$WindowsSetup = @"
@echo off
echo ==========================================
echo  Chronicle Bot - Windows Setup
echo ==========================================
echo.

echo [1/5] Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.11+
    pause
    exit /b 1
)

echo [2/5] Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

echo [3/5] Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install Python dependencies
    pause
    exit /b 1
)

echo [4/5] Installing Node.js dependencies...
npm install
if errorlevel 1 (
    echo ERROR: Failed to install Node.js dependencies
    pause
    exit /b 1
)

echo [5/5] Creating .env file...
if not exist .env (
    copy .env.example .env
    echo .env file created! Please edit it with your configuration.
) else (
    echo .env file already exists, skipping...
)

echo.
echo ==========================================
echo  Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit .env file with your Discord token and database password
echo 2. Create database: psql -U postgres -c "CREATE DATABASE rpg_sessions;"
echo 3. Run database schema: psql -U postgres -d rpg_sessions -f database\schema.sql
echo 4. Start Ollama: ollama serve
echo 5. Pull AI model: ollama pull llama3.2:3b
echo 6. Start bot: python bot\main.py
echo.
pause
"@
$WindowsSetup | Out-File -FilePath "$DistPath\scripts\setup.bat" -Encoding ASCII

Write-Host "  ✓ Created Windows setup script" -ForegroundColor Green

# Step 7: Create .env.example
Write-Host "[7/11] Creating .env.example..." -ForegroundColor Yellow
$EnvExample = @"
# Discord Bot Configuration
DISCORD_TOKEN=your_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/rpg_sessions

# AI Model Configuration
OLLAMA_MODEL=llama3.2:3b
WHISPER_MODEL=base

# Feature Flags
ENABLE_AI_SUMMARY=true
LOG_LEVEL=INFO

# Optional: Advanced Settings
MAX_RECORDING_DURATION=14400
MAX_FILE_SIZE_MB=500
"@
$EnvExample | Out-File -FilePath "$DistPath\.env.example" -Encoding UTF8
Write-Host "  ✓ Created .env.example" -ForegroundColor Green

# Step 8: Create requirements.txt
Write-Host "[8/11] Creating requirements.txt..." -ForegroundColor Yellow
$Requirements = @"
# Chronicle Bot - Python Dependencies
py-cord[voice]==2.7.0
asyncpg==0.29.0
openai-whisper==20231117
ollama==0.4.7
python-dotenv==1.0.0
psutil==5.9.8
wave==0.0.2
"@
$Requirements | Out-File -FilePath "$DistPath\requirements.txt" -Encoding UTF8
Write-Host "  ✓ Created requirements.txt" -ForegroundColor Green

# Step 9: Create package.json
Write-Host "[9/11] Creating package.json..." -ForegroundColor Yellow
$PackageJson = @"
{
  "name": "chronicle-bot",
  "version": "$Version",
  "description": "Discord bot for recording and transcribing RPG sessions",
  "main": "transcript_exporter.js",
  "dependencies": {
    "docx": "^8.5.0"
  },
  "author": "Your Name",
  "license": "SEE LICENSE IN LICENSE"
}
"@
$PackageJson | Out-File -FilePath "$DistPath\package.json" -Encoding UTF8
Write-Host "  ✓ Created package.json" -ForegroundColor Green

# Step 10: Create README.md
Write-Host "[10/11] Creating README.md..." -ForegroundColor Yellow
$Readme = @"
# Chronicle Bot v$Version

🎙️ Record, transcribe, and summarize your RPG sessions with AI!

## Quick Start

1. Install prerequisites (Python 3.11+, Node.js 18+, PostgreSQL 14+, Ollama)
2. Run setup script: ``````scripts\setup.bat`````` (Windows) or ``````./scripts/setup.sh`````` (macOS/Linux)
3. Edit ``.env`````` file with your Discord token and database password
4. Start the bot: ``````python bot\main.py``````

## Features

- ✨ Real-time voice recording
- 🤖 AI transcription with Whisper
- 📖 Story-format summaries with Ollama
- 📄 Professional Word documents
- 💾 Session management
- ⏱️ Chronological conversation ordering

## Documentation

See ``````docs/`````` folder for complete guides.

## System Requirements

- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Ollama
- 8GB RAM (16GB recommended)

## Commands

- ``````/start [name]`````` - Start recording
- ``````/stop`````` - Stop recording
- ``````/transcribe`````` - Generate transcript and summary
- ``````/status`````` - Check bot status

## Support

For help, see the documentation in the ``````docs/`````` folder.

## License

[Your chosen license - see LICENSE file]

---

Made with ❤️ for the RPG community
"@
$Readme | Out-File -FilePath "$DistPath\README.md" -Encoding UTF8
Write-Host "  ✓ Created README.md" -ForegroundColor Green

# Step 11: Create docs folder with placeholder
Write-Host "[11/11] Creating docs folder..." -ForegroundColor Yellow
New-Item -Path "$DistPath\docs" -ItemType Directory | Out-Null
$DocsNote = @"
# Documentation

Please add the following documentation files to this folder:

Required:
- INSTALLATION_GUIDE.md - Step-by-step installation instructions
- LICENSE - Your chosen license file

Optional but recommended:
- LICENSING_GUIDE.md - For monetization information
- DISTRIBUTION_GUIDE.md - For creating distributions
- CHRONOLOGICAL_TRANSCRIPT_UPGRADE.md - For timestamp feature

These files should have been generated separately.
Place them in this docs/ folder before distribution.
"@
$DocsNote | Out-File -FilePath "$DistPath\docs\README.md" -Encoding UTF8
Write-Host "  ✓ Created docs folder" -ForegroundColor Green

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " Distribution Package Created!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Location: $DistPath" -ForegroundColor Green
Write-Host ""
Write-Host "⚠️  IMPORTANT NEXT STEPS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "1. Add schema.sql to database folder:" -ForegroundColor White
Write-Host "   Copy-Item 'schema.sql' '$DistPath\database\' -Force" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Copy documentation to docs folder:" -ForegroundColor White
Write-Host "   Copy-Item 'INSTALLATION_GUIDE.md' '$DistPath\docs\'" -ForegroundColor Gray
Write-Host "   Copy-Item 'LICENSING_GUIDE.md' '$DistPath\docs\'" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Add your LICENSE file:" -ForegroundColor White
Write-Host "   (Choose from LICENSING_GUIDE.md)" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Review and remove any sensitive data" -ForegroundColor White
Write-Host ""
Write-Host "5. Test installation on a clean system" -ForegroundColor White
Write-Host ""
Write-Host "6. Create release archive:" -ForegroundColor White
Write-Host "   Compress-Archive -Path '$DistPath\*' -DestinationPath 'chronicle-bot-v$Version.zip'" -ForegroundColor Gray
Write-Host ""
