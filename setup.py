"""
Setup script for Voice Cloning TTS System
Checks dependencies and helps with installation
"""

import sys
import subprocess
import os

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
    return True

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is installed")
            return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    
    print("❌ FFmpeg is not installed or not in PATH")
    print("   Please install FFmpeg:")
    print("   - Windows: Download from https://ffmpeg.org/download.html")
    print("   - macOS: brew install ffmpeg")
    print("   - Linux: sudo apt install ffmpeg")
    return False

def install_dependencies():
    """Install Python dependencies"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies")
        return False

def create_directories():
    """Create necessary directories"""
    dirs = ['static/audio', 'static/voice_models']
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    print("✅ Directories created")

def main():
    print("=" * 60)
    print("Voice Cloning TTS System - Setup")
    print("=" * 60)
    print()
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    # Install dependencies
    print()
    deps_ok = install_dependencies()
    
    # Create directories
    print()
    create_directories()
    
    # Summary
    print()
    print("=" * 60)
    print("Setup Summary")
    print("=" * 60)
    
    if ffmpeg_ok and deps_ok:
        print("✅ Setup completed successfully!")
        print()
        print("To start the application, run:")
        print("   python app.py")
        print()
        print("Then open your browser to:")
        print("   http://localhost:5000")
    else:
        print("⚠️  Setup completed with warnings")
        if not ffmpeg_ok:
            print("   - Please install FFmpeg for audio processing")
        if not deps_ok:
            print("   - Some dependencies may not have installed correctly")
        print()
        print("Please resolve the issues above before running the application")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
