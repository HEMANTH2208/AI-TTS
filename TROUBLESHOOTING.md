# Troubleshooting Guide

## "Failed to Fetch" Error When Uploading Audio

### Cause
This error occurs when the server encounters an issue processing the uploaded audio file.

### Solutions

#### Solution 1: Install FFmpeg (Recommended)
FFmpeg is required for audio processing. Without it, the system works in basic mode.

**Windows:**
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH:
   - Right-click "This PC" → Properties
   - Advanced system settings → Environment Variables
   - Edit "Path" → Add `C:\ffmpeg\bin`
4. Restart your terminal/command prompt
5. Verify: `ffmpeg -version`
6. Restart the Flask app: `python app.py`

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Solution 2: Check File Format
Supported formats: WAV, MP3, M4A, OGG, WebM

If using a different format, convert it first.

#### Solution 3: Check File Size
- Maximum recommended: 10MB
- For larger files, compress or trim the audio

#### Solution 4: Check Server Logs
Look at the terminal where `python app.py` is running for error messages.

Common errors:
- `No module named 'pyaudioop'` - FFmpeg not installed
- `Permission denied` - Check file permissions
- `File not found` - Check upload path

#### Solution 5: Use Basic Mode (No FFmpeg)
The app will work without FFmpeg but with limited features:
- ✅ Voice upload and storage works
- ✅ Voice model creation works
- ✅ TTS generation works
- ❌ Advanced audio analysis disabled
- ❌ Voice characteristic matching disabled

To use basic mode:
1. Just upload your audio file
2. System will use default characteristics
3. Voice will be saved and usable

---

## Other Common Issues

### Issue: "Microphone access denied"
**Solution:**
1. Check browser permissions (click lock icon in address bar)
2. Allow microphone access for localhost
3. Try Chrome or Firefox (better WebRTC support)

### Issue: "Recording too short"
**Solution:**
- Record for at least 10 seconds
- Recommended: 30+ seconds for better quality

### Issue: Voice doesn't sound like me
**Solution:**
1. Install FFmpeg for voice matching
2. Record longer samples (60+ seconds)
3. Add multiple training samples (3-5)
4. Ensure quality score is 90%+

### Issue: Server won't start
**Solution:**
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000  # Windows
lsof -i :5000                 # macOS/Linux

# Kill the process or use different port
# In app.py, change: app.run(debug=True, port=5001)
```

### Issue: Dependencies not installing
**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# If still failing, install individually
pip install flask
pip install gTTS
pip install pydub
pip install numpy
```

### Issue: "Module not found" errors
**Solution:**
```bash
# Make sure you're in the project directory
cd path/to/AI-TTS

# Activate virtual environment if using one
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Checking System Status

### Check Python Version
```bash
python --version
# Should be 3.8 or higher
```

### Check FFmpeg Installation
```bash
ffmpeg -version
# Should show version info
```

### Check Dependencies
```bash
pip list | grep -E "flask|gTTS|pydub|numpy"
# Should show all packages
```

### Test Audio Processing
```python
# Run in Python console
from pydub import AudioSegment
import numpy as np
print("Audio processing available!")
```

---

## Debug Mode

### Enable Detailed Logging
In `app.py`, add at the top:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Browser Console
1. Open browser DevTools (F12)
2. Go to Console tab
3. Look for JavaScript errors
4. Check Network tab for failed requests

### Check Server Logs
Watch the terminal where `python app.py` is running for:
- File upload confirmations
- Error messages
- Processing status

---

## Performance Issues

### Slow Audio Generation
**Causes:**
- Large text input
- Slow internet (for gTTS)
- Heavy audio processing

**Solutions:**
- Break text into smaller chunks
- Use faster internet connection
- Reduce audio processing (disable FFmpeg features)

### High Memory Usage
**Causes:**
- Multiple large audio files
- Long recordings

**Solutions:**
- Clear old audio files from `static/audio/`
- Reduce recording length
- Restart the server periodically

---

## Getting Help

### Information to Provide
When asking for help, include:
1. Operating system and version
2. Python version (`python --version`)
3. FFmpeg status (`ffmpeg -version`)
4. Error message from terminal
5. Error message from browser console
6. Steps to reproduce the issue

### Useful Commands
```bash
# Check Python version
python --version

# Check installed packages
pip list

# Check FFmpeg
ffmpeg -version

# Check if server is running
curl http://localhost:5000

# View server logs
# (Just look at terminal where app.py is running)
```

---

## Quick Fixes

### Reset Everything
```bash
# Stop the server (Ctrl+C)

# Clear audio files
rm -rf static/audio/*
rm -rf static/voice_models/*

# Reinstall dependencies
pip install -r requirements.txt

# Restart server
python app.py
```

### Fresh Start
```bash
# Create new virtual environment
python -m venv venv_new
source venv_new/bin/activate  # or venv_new\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt

# Run app
python app.py
```

---

## Still Having Issues?

1. Check the main README.md for setup instructions
2. Review INSTALLATION.md for detailed setup
3. Check VOICE_TRAINING_GUIDE.md for usage tips
4. Make sure FFmpeg is installed and in PATH
5. Try the basic mode (without FFmpeg) first
6. Check file permissions on upload directories

---

## Success Checklist

- [ ] Python 3.8+ installed
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] FFmpeg installed and in PATH (optional but recommended)
- [ ] Server starts without errors
- [ ] Can access http://localhost:5000
- [ ] Can upload audio files
- [ ] Can record voice samples
- [ ] Can generate TTS audio

If all checked, you're good to go! 🎉
