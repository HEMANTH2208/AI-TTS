# Installation Guide - Voice Cloning TTS System

## Prerequisites

Before installing, ensure you have:
- Python 3.8 or higher
- pip (Python package manager)
- FFmpeg (required for audio processing)

## Step 1: Install FFmpeg

FFmpeg is required for the pydub library to process audio files.

### Windows:
1. Download FFmpeg from: https://ffmpeg.org/download.html
2. Extract to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH
4. Verify installation: `ffmpeg -version`

### macOS:
```bash
brew install ffmpeg
```

### Linux (Ubuntu/Debian):
```bash
sudo apt update
sudo apt install ffmpeg
```

## Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- Flask (web framework)
- gTTS (Google Text-to-Speech)
- pydub (audio processing)
- numpy (numerical computations)

## Step 3: Run the Application

```bash
python app.py
```

The application will start on `http://127.0.0.1:5000`

## Step 4: Access the Application

Open your web browser and navigate to:
- Homepage: `http://localhost:5000`
- Studio: `http://localhost:5000/studio`

## Features Overview

### Voice Training
1. Navigate to "Voice Studio" tab
2. Click "Start Recording" or upload an audio file
3. Read the provided sample paragraphs (30+ seconds recommended)
4. Submit for training
5. Your custom voice will appear in the TTS tab

### Text-to-Speech
1. Select a voice (standard or your custom trained voice)
2. Enter text to convert
3. Click "Generate Voice"
4. Listen and download the audio

## Voice Characteristics Processing

The system analyzes and applies the following characteristics from your trained voice:

### Pitch Adjustment
- **High Pitch**: +2 semitones shift
- **Medium Pitch**: No adjustment
- **Low Pitch**: -2 semitones shift

### Speed Adjustment
- **Fast**: 1.15x playback speed
- **Normal**: 1.0x playback speed
- **Slow**: 0.85x playback speed

### Tone/Timbre
- **Warm**: Low-pass filter at 3000Hz (emphasizes lower frequencies)
- **Neutral**: No filtering
- **Bright**: High-pass filter at 200Hz (emphasizes higher frequencies)

## How Voice Matching Works

When you use a custom trained voice:

1. **Audio Analysis**: The system analyzes your voice sample to extract:
   - Pitch characteristics (frequency analysis)
   - Speaking speed (temporal analysis)
   - Tone quality (spectral analysis)
   - Audio quality metrics (RMS, amplitude)

2. **Base Generation**: Text is converted to speech using Google TTS

3. **Voice Transformation**: The generated audio is modified to match your voice:
   - Pitch shifting to match your vocal range
   - Speed adjustment to match your speaking pace
   - Frequency filtering to match your tone

4. **Output**: The result sounds closer to your natural voice

## Quality Factors

### Recording Quality
- **Environment**: Quiet room with minimal echo
- **Microphone**: Good quality USB or built-in mic
- **Distance**: 6-12 inches from microphone
- **Volume**: Consistent, moderate volume

### Training Quality Score
- **0-69%**: Poor quality, re-record recommended
- **70-89%**: Good quality, usable
- **90-100%**: Excellent quality, production-ready

### Improving Accuracy
1. Record longer samples (60+ seconds)
2. Add multiple training samples (3-5 recommended)
3. Ensure quiet recording environment
4. Speak clearly and naturally
5. Read all provided sample paragraphs

## Troubleshooting

### "No module named 'pydub'" Error
```bash
pip install pydub
```

### "FFmpeg not found" Error
- Ensure FFmpeg is installed and in your system PATH
- Restart your terminal/command prompt after installation
- Verify with: `ffmpeg -version`

### "Microphone access denied"
- Check browser permissions (usually in address bar)
- Allow microphone access for localhost
- Try a different browser (Chrome/Firefox recommended)

### Poor Voice Quality
- Record in a quieter environment
- Speak closer to the microphone
- Add more training samples
- Record for longer duration (60+ seconds)

### Audio Processing Errors
- Ensure FFmpeg is properly installed
- Check audio file format (WAV, MP3, M4A, OGG, WebM supported)
- Verify file is not corrupted
- Try re-recording or using a different file

## Advanced Configuration

### Voice Cloning Method
In `app.py`, you can configure:

```python
VOICE_CLONING_ENABLED = True  # Enable/disable voice cloning
VOICE_CLONING_METHOD = "local"  # Options: "local", "elevenlabs", "coqui"
```

### Audio Processing Parameters
Modify in `apply_voice_characteristics()` function:

```python
# Pitch shift range
pitch_shift = 2  # Semitones (adjust for more/less pitch change)

# Speed adjustment
speed_factor = 1.15  # Multiplier (1.0 = normal speed)

# Frequency filters
audio.low_pass_filter(3000)  # Adjust cutoff frequency
audio.high_pass_filter(200)   # Adjust cutoff frequency
```

## API Integration (Optional)

For production-grade voice cloning, integrate with:

### Eleven Labs API
```python
# In app.py, add:
import elevenlabs

def generate_with_elevenlabs(text, voice_id):
    audio = elevenlabs.generate(
        text=text,
        voice=voice_id,
        model="eleven_monolingual_v1"
    )
    return audio
```

### Coqui TTS
```python
from TTS.api import TTS

tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text="Hello world", file_path="output.wav")
```

## Performance Optimization

### For Faster Processing:
1. Use shorter text chunks
2. Pre-process audio samples
3. Cache voice characteristics
4. Use faster audio codecs (MP3 instead of WAV)

### For Better Quality:
1. Use higher sample rates (44100Hz or 48000Hz)
2. Record in lossless formats (WAV)
3. Add more training samples
4. Use professional microphone

## Security Considerations

- Voice samples are stored locally on the server
- No data is sent to third-party services (with local method)
- Implement user authentication for production
- Add rate limiting for API endpoints
- Validate and sanitize all user inputs
- Implement HTTPS for production deployment

## Production Deployment

### Using Gunicorn (Linux/macOS):
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Waitress (Windows):
```bash
pip install waitress
waitress-serve --port=5000 app:app
```

### Environment Variables:
```bash
export FLASK_ENV=production
export SECRET_KEY=your-secret-key-here
```

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the VOICE_TRAINING_GUIDE.md
3. Check FFmpeg installation
4. Verify Python dependencies

## License

This project is for educational and research purposes. Ensure you have proper consent before cloning any voice.
