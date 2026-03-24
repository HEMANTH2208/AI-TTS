# 🎙️ Sonic Curator — AI Voice Generation App

A full-stack Flask web application for Text-to-Speech synthesis using Google TTS (gTTS),
with a separate Voice Studio for predefined voice selection, live recording, and voice sample upload.

---

## 📁 Project Structure

```
sonic_curator/
├── app.py                  # Flask backend
├── requirements.txt        # Python dependencies
├── templates/
│   ├── index.html          # Landing page
│   └── studio.html         # Voice Studio (TTS + Cloning)
└── static/
    └── audio/              # Generated MP3 files (auto-created)
```

---

## ⚙️ Setup & Installation

### 1. Create a virtual environment (recommended)
```bash
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the app
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:5000
```

---

## 🌐 Pages

| Route      | Description                                      |
|------------|--------------------------------------------------|
| `/`        | Landing page with features, how-it-works, ethics |
| `/studio`  | TTS Studio + Voice Training Lab                  |

---

## 🔊 Features

### Text-to-Speech (TTS)
- 8 voice profiles across English (US/UK/AU/IN/CA), Spanish, French, Japanese
- Normal and Slow speed modes
- Real-time MP3 generation via Google TTS
- In-browser audio playback
- One-click MP3 download

### Voice Studio
- **Predefined voice library** — browse and use any of the 8 voices
- **File upload** — WAV, MP3, M4A, OGG (drag & drop or click)
- **Live recording** — directly in the browser using the Web Audio API
- Voice sample submission pipeline (ready for Coqui TTS / custom model integration)

---

## 🗣️ Available Voices

| Key          | Name    | Language        | Accent         |
|--------------|---------|-----------------|----------------|
| arthur_us    | Arthur  | English         | US             |
| elena_uk     | Elena   | English         | UK             |
| marcus_au    | Marcus  | English         | Australian     |
| sofia_es     | Sofia   | Spanish         | Castilian      |
| hiroshi_ja   | Hiroshi | Japanese        | Standard       |
| amara_fr     | Amara   | French          | French         |
| ravi_in      | Ravi    | English         | Indian         |
| clara_ca     | Clara   | English         | Canadian       |

---

## 🔌 API Endpoints

| Method | Endpoint            | Description                        |
|--------|---------------------|------------------------------------|
| GET    | `/`                 | Landing page                       |
| GET    | `/studio`           | Studio page                        |
| GET    | `/api/voices`       | List all available voices (JSON)   |
| POST   | `/api/synthesize`   | Generate speech from text          |
| POST   | `/api/upload-clone` | Upload voice sample for training   |

### POST `/api/synthesize`
```json
{
  "text": "Hello world!",
  "voice": "arthur_us",
  "slow": false
}
```
**Response:**
```json
{
  "success": true,
  "audio_url": "/static/audio/<uuid>.mp3",
  "filename": "<uuid>.mp3"
}
```

---

## 🚀 Upgrading to Custom Voice Cloning

The `/api/upload-clone` endpoint saves voice samples locally and is ready to be wired into:
- **Coqui TTS** (`pip install TTS`) for open-source voice cloning
- **ElevenLabs API** for premium voice cloning
- **OpenAI TTS API** for GPT-4o-powered synthesis

---

## ⚖️ Ethics

- Only upload voices you own or have **explicit written permission** to use.
- Never use this tool to create non-consensual voice deepfakes.
- All synthesized audio should be disclosed as AI-generated.

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask
- **TTS Engine:** Google Text-to-Speech (gTTS)
- **Frontend:** HTML, Tailwind CSS, Vanilla JS
- **Fonts:** Manrope (headlines), Inter (body)
- **Icons:** Google Material Symbols
