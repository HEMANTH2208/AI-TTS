# 🎙️ AI Based TTS System with Voice Cloning

An advanced Text-to-Speech system with **custom voice training and cloning capabilities**. Train the system with your voice and generate speech that **matches your tone, pitch, and speaking style**.

---

## 🎯 Key Features

### 🎤 Voice Training & Cloning
- **Record Your Voice**: Capture your unique voice characteristics
- **Multi-Sample Training**: Add multiple samples to improve accuracy up to 100%
- **Quality Scoring**: Real-time feedback on training quality (0-100%)
- **Voice Matching**: Generated speech matches your pitch, speed, and tone
- **Persistent Storage**: Your trained voices are saved and ready to use anytime

### 🔊 Text-to-Speech
- **8 Pre-built Voices**: Professional narrators in multiple languages
- **Custom Voices**: Use your trained voice for any text
- **Streaming Playback**: Sentence-by-sentence audio generation
- **Multiple Formats**: Download as MP3
- **Speed Controls**: Normal/slow modes + playback rate adjustment

### 🎨 Voice Characteristics Matching
The system analyzes and replicates:
- **Pitch**: High, medium, or low vocal range (±2 semitones adjustment)
- **Speed**: Fast, normal, or slow speaking pace (0.85x - 1.15x)
- **Tone**: Warm, neutral, or bright voice quality (frequency filtering)
- **Quality**: Audio clarity and consistency metrics

---

## 🚀 Quick Start

### 1. Installation

```bash
# Run the automated setup script
python setup.py

# Or install manually
pip install -r requirements.txt
```

**⚠️ Important**: FFmpeg is required for audio processing
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 2. Run the Application

```bash
python app.py
```

Open your browser to: **http://localhost:5000**

### 3. Train Your Voice (30 seconds)

1. Navigate to **Voice Studio** tab
2. Click **Start Recording**
3. Read the provided sample paragraphs clearly (30+ seconds recommended)
4. Click **Stop Recording**
5. Enter a name for your voice
6. Click **Submit Voice for Training**
7. Your voice appears in TTS tab with quality score!

### 4. Generate Speech in Your Voice

1. Go to **Text-to-Speech** tab
2. Select your custom trained voice (shows quality %)
3. Enter any text you want to convert
4. Click **Generate Voice**
5. Listen to speech that sounds like you!

---

## 🎙️ How Voice Matching Works

### Training Phase
1. **Audio Analysis**: System extracts voice characteristics
   - Pitch frequency analysis using FFT
   - Speaking speed detection
   - Tone/timbre profiling (spectral analysis)
   - Quality metrics (RMS, amplitude, sample rate)

2. **Model Creation**: Characteristics stored in voice model database
   - Pitch category (high/medium/low)
   - Speed factor (fast/normal/slow)
   - Tone profile (warm/neutral/bright)
   - Sample metadata and quality score

### Generation Phase
1. **Base Audio**: Text converted to speech using Google TTS
2. **Voice Transformation**: Audio modified to match your voice characteristics
   - **Pitch Shifting**: ±2 semitones based on your vocal range
   - **Speed Adjustment**: 0.85x - 1.15x based on your speaking pace
   - **Frequency Filtering**: Tone matching (warm/bright)
3. **Output**: Speech that sounds like your voice!

---

## 📊 Quality Scoring System

### Score Calculation
```
Base Quality = (duration / 60) * 100  (max 100%)
Sample Bonus = sample_count * 5%      (max +20%)
Audio Quality Bonus = +3-5%           (for clear audio)
Final Score = min(100, Base + Bonuses)
```

### Quality Factors
- **Duration**: Longer recordings capture more characteristics
  - 10s minimum (required)
  - 30s recommended
  - 60s+ optimal (100% base quality)
- **Sample Count**: Multiple samples improve accuracy
  - +5% per additional sample
  - Up to +20% bonus for 4+ samples
- **Audio Quality**: Clear recordings score higher
  - Low background noise
  - Consistent volume
  - Good microphone quality

### Quality Levels
- 🟢 **90-100%**: Excellent - Production ready, sounds very natural
- 🟡 **70-89%**: Good - Usable quality, minor differences
- 🟠 **<70%**: Poor - Re-record recommended for better results

---

## 🎨 User Interface Features

### Voice Training Lab
- 📤 Drag & drop audio upload (WAV, MP3, M4A, OGG, WebM)
- 🎤 Live recording with visual waveform feedback
- 📝 Reading prompts displayed during recording (center screen)
- 📊 Real-time quality indicator with progress bar
- 💡 Training tips and recommendations
- ➕ Add multiple samples to improve accuracy
- 🎯 Quality score with color-coded feedback

### TTS Studio
- 🎭 Voice selection grid (8 standard + your custom voices)
- ⌨️ Real-time character counter (0/3000)
- ⚡ Speed controls (normal/slow)
- 🎚️ Playback rate adjustment (1x, 1.5x, 2x)
- 📊 Animated waveform visualization (pauses when not playing)
- 💾 Download generated audio as MP3
- ℹ️ Custom voice indicator showing your voice characteristics

---

## 🔧 Technical Details

### Backend (Python/Flask)
```python
# Voice model storage and management
- JSON database for metadata
- File-based audio storage
- Audio analysis with pydub and numpy
- Pitch shifting and speed adjustment
- Frequency filtering for tone matching
- Quality scoring algorithm
```

### Audio Processing Pipeline
```python
# 1. Analyze uploaded voice sample
characteristics = analyze_audio_characteristics(audio_file)
# Returns: pitch, speed, tone, quality_metrics

# 2. Generate base audio with gTTS
tts = gTTS(text=text, lang="en")
tts.save("base_audio.mp3")

# 3. Apply voice characteristics
apply_voice_characteristics(
    input="base_audio.mp3",
    characteristics=user_voice_profile,
    output="final_audio.mp3"
)
# Applies: pitch shift, speed adjustment, tone filtering
```

### Frontend (JavaScript)
- MediaRecorder API for voice capture
- Real-time waveform animations (play/pause sync)
- LocalStorage for model persistence
- Responsive design with Tailwind CSS
- Modal reading prompts during recording

---

## 📁 Project Structure

```
├── app.py                      # Flask backend with voice processing
├── requirements.txt            # Python dependencies
├── setup.py                   # Automated setup script
├── templates/
│   ├── index.html             # Landing page with features
│   └── studio.html            # TTS & training interface
├── static/
│   ├── audio/                 # Generated audio files (temp)
│   └── voice_models/          # Trained voice models
│       ├── models.json        # Voice metadata database
│       └── voice_*.webm       # Voice sample files
├── INSTALLATION.md            # Detailed setup guide
├── VOICE_TRAINING_GUIDE.md    # Training best practices
└── README.md                  # This file
```

---

## 🎯 Best Practices for Voice Training

### Recording Environment
- ✅ Quiet room with minimal echo and background noise
- ✅ Good quality microphone (USB or built-in)
- ✅ 6-12 inches from microphone
- ✅ Consistent volume throughout recording

### Recording Technique
- ✅ Speak naturally at your normal pace
- ✅ Read all provided sample paragraphs completely
- ✅ Clear pronunciation without over-enunciating
- ✅ Natural pauses at punctuation marks
- ✅ Maintain consistent tone and energy

### Multiple Samples Strategy
- ✅ Record 2-3 samples minimum for good quality
- ✅ Vary your tone slightly between samples
- ✅ Each sample should be 30+ seconds
- ✅ Record at different times if possible
- ✅ Aim for 90%+ quality score

---

## 🗣️ Available Voices

### Standard Voices (8)
| Key          | Name    | Language        | Accent         | Gender |
|--------------|---------|-----------------|----------------|--------|
| arthur_us    | Arthur  | English         | US             | Male   |
| elena_uk     | Elena   | English         | UK             | Female |
| marcus_au    | Marcus  | English         | Australian     | Male   |
| sofia_es     | Sofia   | Spanish         | Castilian      | Female |
| hiroshi_ja   | Hiroshi | Japanese        | Standard       | Male   |
| amara_fr     | Amara   | French          | French         | Female |
| ravi_in      | Ravi    | English         | Indian         | Male   |
| clara_ca     | Clara   | English         | Canadian       | Female |

### Custom Voices (Unlimited)
- Train as many custom voices as you want
- Each voice shows quality score
- Stored locally with full metadata
- Can be improved with additional samples

---

## 🔌 API Endpoints

### Voice Training
```http
POST /api/upload-clone
Content-Type: multipart/form-data

audio: <audio_file>
voice_name: "My Voice"
training_text: "Sample text that was read"
duration: 45.2
```

**Response:**
```json
{
  "success": true,
  "model_id": "voice_abc123",
  "quality_score": 85,
  "characteristics": {
    "pitch": "medium",
    "speed": "normal",
    "tone": "neutral"
  },
  "recommendations": [
    "Good quality. Consider adding more samples for best results"
  ]
}
```

### Add Training Sample
```http
POST /api/add-training-sample
Content-Type: multipart/form-data

audio: <audio_file>
model_id: "voice_abc123"
duration: 30.5
```

### Text-to-Speech
```http
POST /api/synthesize
Content-Type: application/json

{
  "text": "Hello, this is my custom voice!",
  "voice": "voice_abc123",
  "slow": false
}
```

**Response:**
```json
{
  "success": true,
  "audio_url": "/static/audio/xyz789.mp3",
  "voice_type": "custom",
  "voice_name": "My Voice"
}
```

### Voice Management
```http
GET  /api/voice-models              # List all trained voices
GET  /api/voice-model/<model_id>    # Get specific voice details
DELETE /api/voice-model/<model_id>  # Delete voice model
```

---

## 🐛 Troubleshooting

### FFmpeg Not Found
```bash
# Verify installation
ffmpeg -version

# Windows: Add to PATH
setx PATH "%PATH%;C:\ffmpeg\bin"

# Restart terminal/command prompt
```

### Poor Voice Quality
- ✅ Record in quieter environment
- ✅ Use better microphone
- ✅ Add 2-3 more training samples
- ✅ Record for 60+ seconds
- ✅ Speak closer to microphone

### Microphone Access Denied
- ✅ Check browser permissions (address bar icon)
- ✅ Allow microphone for localhost
- ✅ Try Chrome or Firefox
- ✅ Check system microphone settings

### Audio Processing Errors
- ✅ Ensure FFmpeg is installed and in PATH
- ✅ Check audio file format (supported: WAV, MP3, M4A, OGG, WebM)
- ✅ Verify file is not corrupted
- ✅ Try re-recording or different file

### Voice Doesn't Sound Like Me
- ✅ Add more training samples (3-5 recommended)
- ✅ Record longer samples (60+ seconds)
- ✅ Ensure consistent recording quality
- ✅ Check quality score is 90%+

---

## 🔒 Privacy & Ethics

### Privacy
- ✅ Voice samples stored locally on your server
- ✅ No third-party API calls (local processing)
- ✅ No data sent to external services
- ✅ Easy model deletion for privacy
- ✅ User consent required for recording

### Ethics
- ⚠️ **Only train voices you own or have explicit permission to use**
- ⚠️ Never create non-consensual voice deepfakes
- ⚠️ Disclose AI-generated audio when sharing
- ⚠️ Respect voice ownership and privacy rights
- ⚠️ Follow local laws regarding voice synthesis

---

## 🚀 Advanced Configuration

### Voice Processing Parameters
```python
# In app.py - adjust these for different results

# Pitch shift range (semitones)
pitch_shift = 2  # ±2 semitones (adjust for more/less change)

# Speed adjustment multiplier
speed_factor = 1.15  # 1.0 = normal (0.5-2.0 range)

# Frequency filters (Hz)
audio.low_pass_filter(3000)   # Warm tone
audio.high_pass_filter(200)   # Bright tone
```

### Integration with Premium APIs
```python
# Eleven Labs (premium quality)
import elevenlabs
audio = elevenlabs.generate(text=text, voice=voice_id)

# Coqui TTS (open source)
from TTS.api import TTS
tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
```

---

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)** - Detailed setup instructions
- **[Voice Training Guide](VOICE_TRAINING_GUIDE.md)** - Best practices and tips

---

## 🔮 Future Enhancements

- [ ] Real-time pitch detection during recording
- [ ] Emotion-specific voice training (happy, sad, excited)
- [ ] Multi-language voice cloning
- [ ] Neural network-based voice synthesis
- [ ] Cloud-based processing options
- [ ] Batch audio generation
- [ ] Voice mixing and blending
- [ ] Professional voice coaching tips
- [ ] Advanced audio quality analysis

---

## 🛠️ Tech Stack

- **Backend:** Python 3.8+, Flask
- **TTS Engine:** Google Text-to-Speech (gTTS)
- **Audio Processing:** pydub, numpy, FFmpeg
- **Frontend:** HTML5, Tailwind CSS, Vanilla JavaScript
- **APIs:** MediaRecorder, Web Audio API
- **Fonts:** Manrope (headlines), Inter (body)
- **Icons:** Google Material Symbols

---

## 📄 License

This project is for educational and research purposes. Always obtain proper consent before cloning any voice.

---

## 🤝 Contributing

Contributions welcome! Please ensure:
- Code follows existing style
- Audio processing is efficient
- User privacy is maintained
- Ethical guidelines are followed
- Documentation is updated

---

**Made with ❤️ for voice synthesis enthusiasts**

*Transform text into your voice with AI-powered voice cloning*
