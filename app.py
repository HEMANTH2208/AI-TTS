from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS
import os
import uuid
import time

app = Flask(__name__)

AUDIO_DIR = os.path.join("static", "audio")
os.makedirs(AUDIO_DIR, exist_ok=True)

# Available gTTS voices (language + tld combos for accent variation)
VOICES = {
    "arthur_us": {"name": "Arthur", "desc": "Professional Narrator", "lang": "en", "tld": "com", "gender": "male"},
    "elena_uk": {"name": "Elena", "desc": "Conversational Tech (UK)", "lang": "en", "tld": "co.uk", "gender": "female"},
    "marcus_au": {"name": "Marcus", "desc": "Deep & Resonant (AU)", "lang": "en", "tld": "com.au", "gender": "male"},
    "sofia_es": {"name": "Sofia", "desc": "Spanish (Castilian)", "lang": "es", "tld": "es", "gender": "female"},
    "hiroshi_ja": {"name": "Hiroshi", "desc": "Japanese Standard", "lang": "ja", "tld": "com", "gender": "male"},
    "amara_fr": {"name": "Amara", "desc": "French Conversational", "lang": "fr", "tld": "fr", "gender": "female"},
    "ravi_in": {"name": "Ravi", "desc": "Indian English", "lang": "en", "tld": "co.in", "gender": "male"},
    "clara_ca": {"name": "Clara", "desc": "Canadian English", "lang": "en", "tld": "ca", "gender": "female"},
}


def cleanup_old_files():
    """Remove audio files older than 10 minutes."""
    now = time.time()
    for f in os.listdir(AUDIO_DIR):
        fpath = os.path.join(AUDIO_DIR, f)
        if os.path.isfile(fpath) and now - os.path.getmtime(fpath) > 600:
            try:
                os.remove(fpath)
            except Exception:
                pass


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/studio")
def studio():
    return render_template("studio.html", voices=VOICES)


@app.route("/api/synthesize", methods=["POST"])
def synthesize():
    cleanup_old_files()
    data = request.get_json()

    text = data.get("text", "").strip()
    voice_key = data.get("voice", "arthur_us")
    slow = data.get("slow", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 3000:
        return jsonify({"error": "Text too long (max 3000 characters)"}), 400

    voice = VOICES.get(voice_key, VOICES["arthur_us"])

    try:
        tts = gTTS(text=text, lang=voice["lang"], tld=voice["tld"], slow=slow)
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        tts.save(filepath)
        return jsonify({"success": True, "audio_url": f"/static/audio/{filename}", "filename": filename})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/synthesize-chunk", methods=["POST"])
def synthesize_chunk():
    cleanup_old_files()
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    voice_key = data.get("voice", "arthur_us")
    slow = data.get("slow", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400

    voice = VOICES.get(voice_key, VOICES["arthur_us"])
    try:
        filename = f"{uuid.uuid4().hex}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        tts = gTTS(text=text, lang=voice["lang"], tld=voice["tld"], slow=slow)
        tts.save(filepath)
        return jsonify({"success": True, "audio_url": f"/static/audio/{filename}", "chunk_text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/voices", methods=["GET"])
def get_voices():
    return jsonify(VOICES)


@app.route("/api/upload-clone", methods=["POST"])
def upload_clone():
    """Receive uploaded voice sample — simulated processing."""
    if "audio" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["audio"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    allowed = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in allowed:
        return jsonify({"error": "Unsupported format"}), 400

    filename = f"clone_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(AUDIO_DIR, filename)
    file.save(filepath)

    return jsonify({
        "success": True,
        "message": "Voice sample received. In a full deployment, this would train a custom voice model.",
        "sample_id": filename
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
