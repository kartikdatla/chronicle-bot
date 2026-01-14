"""
Chronicle Bot Installation Validator
Tests that all components are properly installed and working
"""

import sys
from pathlib import Path

def test_python_version():
    """Test Python version"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor} (need 3.10+)")
        return False

def test_python_packages():
    """Test required Python packages"""
    print("\n📦 Testing Python packages...")
    required = {
        'discord': 'py-cord',
        'asyncpg': 'asyncpg',
        'whisper': 'openai-whisper',
        'dotenv': 'python-dotenv',
        'docx': 'python-docx',
        'ollama': 'ollama'
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - Run: pip install {package}")
            all_ok = False
    
    return all_ok

def test_nodejs():
    """Test Node.js and npm"""
    print("\n🟢 Testing Node.js...")
    import subprocess
    
    all_ok = True
    
    # Test node
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ Node.js {result.stdout.strip()}")
        else:
            print(f"   ❌ Node.js not found")
            all_ok = False
    except FileNotFoundError:
        print(f"   ❌ Node.js not installed")
        all_ok = False
    
    # Test npm
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ npm {result.stdout.strip()}")
        else:
            print(f"   ❌ npm not found")
            all_ok = False
    except FileNotFoundError:
        print(f"   ❌ npm not installed")
        all_ok = False
    
    return all_ok

def test_nodejs_packages():
    """Test Node.js packages"""
    print("\n📦 Testing Node.js packages...")
    
    package_json = Path('package.json')
    if not package_json.exists():
        print("   ❌ package.json not found")
        return False
    
    node_modules = Path('node_modules')
    if not node_modules.exists():
        print("   ❌ node_modules not found - Run: npm install")
        return False
    
    required = ['docx', 'docx-templates']
    all_ok = True
    
    for package in required:
        if (node_modules / package).exists():
            print(f"   ✅ {package}")
        else:
            print(f"   ❌ {package} - Run: npm install")
            all_ok = False
    
    return all_ok

def test_postgresql():
    """Test PostgreSQL connection"""
    print("\n🐘 Testing PostgreSQL...")
    import subprocess
    
    try:
        result = subprocess.run(['psql', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"   ✅ {result.stdout.strip()}")
            return True
        else:
            print(f"   ❌ PostgreSQL not found")
            return False
    except FileNotFoundError:
        print(f"   ❌ PostgreSQL not installed")
        return False

def test_database_connection():
    """Test database connection"""
    print("\n🔌 Testing database connection...")
    
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("   ❌ DATABASE_URL not found in .env")
        return False
    
    try:
        import asyncpg
        import asyncio
        
        async def test_conn():
            try:
                conn = await asyncpg.connect(db_url)
                await conn.close()
                return True
            except Exception as e:
                print(f"   ❌ Connection failed: {e}")
                return False
        
        result = asyncio.run(test_conn())
        if result:
            print("   ✅ Database connection successful")
        return result
        
    except Exception as e:
        print(f"   ❌ Connection test failed: {e}")
        return False

def test_ollama():
    """Test Ollama installation"""
    print("\n🤖 Testing Ollama...")
    import subprocess
    
    try:
        result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
        if result.returncode == 0:
            if 'llama3.2:3b' in result.stdout:
                print(f"   ✅ Ollama installed with llama3.2:3b")
                return True
            else:
                print(f"   ⚠️  Ollama installed but llama3.2:3b not found")
                print(f"   Run: ollama pull llama3.2:3b")
                return False
        else:
            print(f"   ❌ Ollama not responding")
            return False
    except FileNotFoundError:
        print(f"   ❌ Ollama not installed")
        return False

def test_discord_token():
    """Test Discord token"""
    print("\n🤖 Testing Discord bot configuration...")
    
    from dotenv import load_dotenv
    import os
    load_dotenv()
    
    token = os.getenv('DISCORD_TOKEN')
    if not token or token == 'your_discord_bot_token_here':
        print("   ❌ DISCORD_TOKEN not configured in .env")
        return False
    
    print("   ✅ DISCORD_TOKEN found in .env")
    return True

def test_file_structure():
    """Test required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        'bot/main.py',
        'bot/voice_manager.py',
        'bot/transcription_orchestrator.py',
        'bot/summary_generator.py',
        'database/schema.sql',
        'transcript_exporter.js',
        'requirements.txt',
        'package.json',
        '.env'
    ]
    
    all_ok = True
    for file in required_files:
        if Path(file).exists():
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} missing")
            all_ok = False
    
    return all_ok

def main():
    """Run all tests"""
    print("=" * 60)
    print("Chronicle Bot Installation Validator v1.1.0")
    print("=" * 60)
    
    results = {
        'Python Version': test_python_version(),
        'Python Packages': test_python_packages(),
        'Node.js': test_nodejs(),
        'Node.js Packages': test_nodejs_packages(),
        'PostgreSQL': test_postgresql(),
        'Database Connection': test_database_connection(),
        'Ollama': test_ollama(),
        'Discord Token': test_discord_token(),
        'File Structure': test_file_structure()
    }
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test}")
    
    passed_count = sum(results.values())
    total_count = len(results)
    
    print(f"\nPassed: {passed_count}/{total_count}")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Chronicle Bot is ready to use.")
        print("\nNext steps:")
        print("1. Run: python bot/main.py")
        print("2. Invite bot to Discord server")
        print("3. Use /start to begin recording")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Python packages: pip install -r requirements.txt")
        print("- Node packages: npm install")
        print("- Ollama model: ollama pull llama3.2:3b")
        print("- Discord token: Edit .env file")
        return 1

if __name__ == '__main__':
    sys.exit(main())