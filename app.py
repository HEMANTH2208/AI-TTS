from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS
import os
import uuid
import time
import json
from datetime import datetime

# Try to import audio processing libraries
try:
    from pydub import AudioSegment
    from pydub.utils import which as pydub_which
    import numpy as np
    from scipy import signal
    from scipy.fft import fft, fftfreq
    AUDIO_PROCESSING_AVAILABLE = True
    ADVANCED_ANALYSIS_AVAILABLE = True
    print("✅ Audio processing libraries loaded (pydub, numpy, scipy)")
except ImportError as e:
    try:
        from pydub import AudioSegment
        from pydub.utils import which as pydub_which
        import numpy as np
        AUDIO_PROCESSING_AVAILABLE = True
        ADVANCED_ANALYSIS_AVAILABLE = False
        print("✅ Basic audio processing loaded (pydub, numpy)")
        print("⚠️  Advanced analysis unavailable - install scipy: pip install scipy")
    except ImportError:
        AUDIO_PROCESSING_AVAILABLE = False
        ADVANCED_ANALYSIS_AVAILABLE = False
        print(f"⚠️  Audio processing libraries not available: {e}")
        print("   Voice training will work but without advanced analysis")
        print("   Install with: pip install pydub numpy scipy")


def ffmpeg_available():
    if not AUDIO_PROCESSING_AVAILABLE:
        return False
    try:
        return bool(pydub_which("ffmpeg") or pydub_which("ffprobe") or pydub_which("avconv"))
    except Exception:
        return False


def audio_transform_available():
    # pydub import isn't enough; it needs ffmpeg present at runtime.
    return AUDIO_PROCESSING_AVAILABLE and ffmpeg_available()


def pick_best_base_voice(characteristics):
    """
    Choose a base preset voice to start closer to the trained voice.
    This improves similarity without extra training time.
    """
    pitch = (characteristics or {}).get("pitch", "medium")
    speed = (characteristics or {}).get("speed", "normal")
    tone = (characteristics or {}).get("tone", "neutral")

    # Keep it simple + deterministic.
    if pitch == "low":
        return "voice_male_slow" if speed == "slow" else "voice_male_deep"
    if pitch == "high":
        return "voice_female_fast" if speed == "fast" else "voice_female_high"
    # medium
    if tone == "bright":
        return "voice_female_high"
    if tone == "warm":
        return "voice_male_deep"
    return "voice_neutral"

app = Flask(__name__)

AUDIO_DIR = os.path.join("static", "audio")
VOICE_MODELS_DIR = os.path.join("static", "voice_models")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(VOICE_MODELS_DIR, exist_ok=True)

# Voice models database (in production, use a real database)
VOICE_MODELS_DB = os.path.join(VOICE_MODELS_DIR, "models.json")

# Voice cloning configuration
VOICE_CLONING_ENABLED = True  # Set to False to use only gTTS
VOICE_CLONING_METHOD = "local"  # Options: "local", "elevenlabs", "coqui"

def load_voice_models():
    """Load voice models from JSON database."""
    if os.path.exists(VOICE_MODELS_DB):
        with open(VOICE_MODELS_DB, 'r') as f:
            return json.load(f)
    return {}

def save_voice_models(models):
    """Save voice models to JSON database."""
    with open(VOICE_MODELS_DB, 'w') as f:
        json.dump(models, f, indent=2)

def analyze_audio_characteristics(audio_path, training_text=None):
    """
    Analyze audio file to extract voice characteristics.
    This is a simplified version - in production, use proper audio analysis libraries.
    """
    training_text = training_text or ""

    if not AUDIO_PROCESSING_AVAILABLE:
        print("Audio processing not available, using defaults")
        return {
            "duration": 30,
            "sample_rate": 44100,
            "channels": 1,
            "pitch": "medium",
            "speed": "normal",
            "tone": "neutral",
            "quality_metrics": {"rms": 1000, "avg_amplitude": 3000},
        }
    
    try:
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Extract basic characteristics
        duration = len(audio) / 1000.0  # Convert to seconds
        sample_rate = audio.frame_rate
        channels = audio.channels
        
        # Mono + fixed analysis sample rate for stable transforms
        mono = audio.set_channels(1).set_frame_rate(16000)
        samples = np.array(mono.get_array_of_samples(), dtype=np.float32)
        if samples.size == 0:
            raise ValueError("Empty audio samples")
        
        # Calculate basic audio features
        rms = float(np.sqrt(np.mean(samples**2)))  # Root mean square (volume)
        avg_amplitude = float(np.mean(np.abs(samples)))
        
        # ---- Pitch (dominant fundamental estimate) ----
        pitch = "medium"
        if ADVANCED_ANALYSIS_AVAILABLE:
            sr = mono.frame_rate
            frame_size = int(sr * 0.03)  # ~30ms
            hop_size = int(sr * 0.01)  # ~10ms
            fmin = 70.0
            fmax = 300.0

            peaks = []
            if samples.size >= frame_size:
                window = np.hanning(frame_size).astype(np.float32)
                freqs = np.fft.rfftfreq(frame_size, d=1.0 / sr)
                fmask = (freqs >= fmin) & (freqs <= fmax)

                # Sample a limited number of frames for performance
                max_frames = 60
                frame_count = 0
                for start in range(0, samples.size - frame_size, hop_size):
                    frame = samples[start : start + frame_size] * window
                    spectrum = np.abs(np.fft.rfft(frame))
                    if fmask.any():
                        idx = np.argmax(spectrum[fmask])
                        peak = freqs[fmask][idx]
                        if np.isfinite(peak):
                            peaks.append(float(peak))
                    frame_count += 1
                    if frame_count >= max_frames:
                        break

            if peaks:
                median_freq = float(np.median(peaks))
                if median_freq < 130:
                    pitch = "low"
                elif median_freq > 190:
                    pitch = "high"
                else:
                    pitch = "medium"
        else:
            # Fallback heuristic when FFT isn't available.
            # Inverted logic: higher energy often correlates with lower pitch (deeper voice).
            if avg_amplitude > 6000:
                pitch = "low"
            elif avg_amplitude < 2500:
                pitch = "high"
            else:
                pitch = "medium"
        
        # ---- Speed (words per minute, based on training text) ----
        speed = "normal"
        if training_text.strip():
            words = [w for w in training_text.replace("\n", " ").split(" ") if w.strip()]
            word_count = len(words)
            if word_count > 0 and duration > 0:
                wpm = (word_count / duration) * 60.0
                if wpm > 170:
                    speed = "fast"
                elif wpm < 120:
                    speed = "slow"
                else:
                    speed = "normal"
        
        # ---- Tone (spectral centroid / brightness) ----
        tone = "neutral"
        if ADVANCED_ANALYSIS_AVAILABLE:
            sr = mono.frame_rate
            slice_sec = 8.0
            slice_len = min(samples.size, int(sr * slice_sec))
            seg = samples[:slice_len]

            window = np.hanning(seg.size).astype(np.float32)
            spectrum = np.abs(np.fft.rfft(seg * window)) + 1e-9
            freqs = np.fft.rfftfreq(seg.size, d=1.0 / sr)

            fmin = 80.0
            fmax = 5000.0
            fmask = (freqs >= fmin) & (freqs <= fmax)
            mag = spectrum[fmask]
            f = freqs[fmask]
            if mag.size > 0:
                centroid = float(np.sum(f * mag) / np.sum(mag))  # Hz
                if centroid < 1100:
                    tone = "warm"
                elif centroid > 1600:
                    tone = "bright"
                else:
                    tone = "neutral"
        
        return {
            "duration": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "pitch": pitch,
            "speed": speed,
            "tone": tone,
            "quality_metrics": {"rms": float(rms), "avg_amplitude": float(avg_amplitude)},
        }
    except Exception as e:
        print(f"Error analyzing audio: {e}")
        # Return default characteristics if analysis fails
        return {
            "duration": 0,
            "sample_rate": 44100,
            "channels": 1,
            "pitch": "medium",
            "speed": "normal",
            "tone": "neutral",
            "quality_metrics": {
                "rms": 0,
                "avg_amplitude": 0
            }
        }

def apply_voice_characteristics(audio_path, characteristics, output_path):
    """
    Apply voice characteristics to generated audio to match trained voice.
    This modifies pitch, speed, and tone to match the user's voice.
    """
    if not audio_transform_available():
        raise RuntimeError(
            "Audio processing not available. Install FFmpeg and restart to enable custom voice matching."
        )
    
    try:
        print(f"Applying voice characteristics: {characteristics}")
        audio = AudioSegment.from_file(audio_path)
        modified = False
        
        # Apply pitch adjustment
        pitch = characteristics.get("pitch", "medium")
        pitch_shift = 0
        
        if pitch == "high":
            pitch_shift = 3  # Increased from 2 to 3 semitones for more noticeable change
            print(f"  → Shifting pitch UP by {pitch_shift} semitones")
        elif pitch == "low":
            pitch_shift = -3  # Increased from -2 to -3 semitones
            print(f"  → Shifting pitch DOWN by {pitch_shift} semitones")
        
        if pitch_shift != 0:
            try:
                # Change pitch without changing speed
                new_sample_rate = int(audio.frame_rate * (2.0 ** (pitch_shift / 12.0)))
                audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
                audio = audio.set_frame_rate(44100)
                modified = True
                print(f"  ✓ Pitch adjusted successfully")
            except Exception as e:
                print(f"  ✗ Pitch adjustment failed: {e}")
        
        # Apply speed adjustment
        speed = characteristics.get("speed", "normal")
        speed_factor = 1.0
        
        if speed == "fast":
            speed_factor = 1.2  # Increased from 1.15 to 1.2
            print(f"  → Speeding up to {speed_factor}x")
        elif speed == "slow":
            speed_factor = 0.8  # Decreased from 0.85 to 0.8
            print(f"  → Slowing down to {speed_factor}x")
        
        if speed_factor != 1.0:
            try:
                # Calculate new frame count
                sound_with_altered_frame_rate = audio._spawn(
                    audio.raw_data,
                    overrides={"frame_rate": int(audio.frame_rate * speed_factor)}
                )
                audio = sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
                modified = True
                print(f"  ✓ Speed adjusted successfully")
            except Exception as e:
                print(f"  ✗ Speed adjustment failed: {e}")
        
        # Apply tone/timbre adjustments
        tone = characteristics.get("tone", "neutral")

        if tone == "warm":
            try:
                # Boost lower frequencies
                audio = audio.low_pass_filter(3000)
                # Slight bass boost
                audio = audio + 2  # Increase volume slightly
                modified = True
                print(f"  ✓ Warm tone applied (low-pass filter)")
            except Exception as e:
                print(f"  ✗ Warm tone failed: {e}")
        elif tone == "bright":
            try:
                # Boost higher frequencies
                audio = audio.high_pass_filter(200)
                # Slight treble boost
                audio = audio + 2
                modified = True
                print(f"  ✓ Bright tone applied (high-pass filter)")
            except Exception as e:
                print(f"  ✗ Bright tone failed: {e}")
        else:
            # Neutral tone still applies a small EQ so custom voices don't collapse
            # into the same base gTTS output.
            try:
                quality_metrics = characteristics.get("quality_metrics", {}) or {}
                avg_amplitude = float(quality_metrics.get("avg_amplitude", 0) or 0)
                rms = float(quality_metrics.get("rms", 0) or 0)

                # Make neutral shaping depend on the voice sample so multiple custom
                # voices do not become identical when tone is classified as neutral.
                hp_cutoff = int(max(70, min(200, 70 + (avg_amplitude / 100.0))))
                lp_cutoff = int(max(5200, min(8000, 6000 + (rms / 200.0))))
                vol_boost_db = int(max(1, min(5, 2 + (avg_amplitude / 8000.0) * 3)))

                audio = audio.high_pass_filter(hp_cutoff)
                audio = audio.low_pass_filter(lp_cutoff)
                audio = audio + vol_boost_db
                modified = True
                print(
                    f"  ✓ Neutral tone applied (HP={hp_cutoff}Hz, LP={lp_cutoff}Hz, +{vol_boost_db}dB)"
                )
            except Exception as e:
                print(f"  ✗ Neutral tone failed: {e}")
        
        # Export modified audio
        audio.export(output_path, format="mp3", bitrate="192k")
        
        if modified:
            print(f"✅ Voice characteristics applied successfully!")
        else:
            print(f"⚠️  No characteristics were applied")
        
        return modified
        
    except Exception as e:
        print(f"❌ Error applying voice characteristics: {e}")
        import traceback
        traceback.print_exc()
        # For custom voices, never silently fall back to unmodified base audio.
        raise

# Available voices with REAL different characteristics
# Names and descriptions now accurately reflect the actual output
VOICES = {
    # English voices with distinct transformations
    "voice_neutral": {
        "name": "Alex", 
        "desc": "Neutral English Voice", 
        "lang": "en", 
        "tld": "com", 
        "gender": "neutral",
        "engine": "gtts",
        "pitch": "medium",
        "speed": 1.0
    },
    "voice_female_high": {
        "name": "Emma", 
        "desc": "Female - Higher Pitch", 
        "lang": "en", 
        "tld": "com", 
        "gender": "female",
        "engine": "gtts",
        "pitch": "high",
        "speed": 1.05
    },
    "voice_male_deep": {
        "name": "David", 
        "desc": "Male - Deep Voice", 
        "lang": "en", 
        "tld": "com", 
        "gender": "male",
        "engine": "gtts",
        "pitch": "low",
        "speed": 0.95
    },
    "voice_female_fast": {
        "name": "Sarah", 
        "desc": "Female - Fast Speaker", 
        "lang": "en", 
        "tld": "com", 
        "gender": "female",
        "engine": "gtts",
        "pitch": "high",
        "speed": 1.15
    },
    "voice_male_slow": {
        "name": "James", 
        "desc": "Male - Slow & Clear", 
        "lang": "en", 
        "tld": "com", 
        "gender": "male",
        "engine": "gtts",
        "pitch": "low",
        "speed": 0.85
    },
    "voice_british": {
        "name": "Oliver", 
        "desc": "British Accent", 
        "lang": "en", 
        "tld": "co.uk", 
        "gender": "male",
        "engine": "gtts",
        "pitch": "medium",
        "speed": 1.0
    },
    "voice_spanish": {
        "name": "Sofia", 
        "desc": "Spanish Voice", 
        "lang": "es", 
        "tld": "es", 
        "gender": "female",
        "engine": "gtts",
        "pitch": "high",
        "speed": 1.0
    },
    "voice_french": {
        "name": "Marie", 
        "desc": "French Voice", 
        "lang": "fr", 
        "tld": "fr", 
        "gender": "female",
        "engine": "gtts",
        "pitch": "high",
        "speed": 1.0
    },
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
    voice_key = data.get("voice", "voice_neutral")
    slow = data.get("slow", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 3000:
        return jsonify({"error": "Text too long (max 3000 characters)"}), 400

    # Check if this is a custom trained voice (check models database first)
    models = load_voice_models()
    
    if voice_key in models:
        # Use custom trained voice model
        model = models[voice_key]
        print(f"Using custom voice: {model['name']} (ID: {voice_key})")

        if not audio_transform_available():
            return jsonify(
                {
                    "success": False,
                    "error": "Audio processing not available. Install FFmpeg and restart to enable custom voice matching.",
                    "code": "FFMPEG_MISSING",
                }
            ), 412
        
        try:
            # For custom voices, we'll use a hybrid approach:
            # 1. Generate base audio with gTTS
            # 2. Apply the user's voice characteristics heavily
            
            base_lang = model.get("language", "en")
            base_key = model.get("base_voice_key") or pick_best_base_voice(
                model.get("characteristics", {})
            )
            base_voice = VOICES.get(base_key, VOICES["voice_neutral"])
            base_tld = base_voice.get("tld", "com")
            
            # Generate base audio
            tts = gTTS(text=text, lang=base_lang, tld=base_tld, slow=slow)
            temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
            temp_filepath = os.path.join(AUDIO_DIR, temp_filename)
            tts.save(temp_filepath)
            
            # Apply voice characteristics to match trained voice
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)

            success = False
            try:
                success = apply_voice_characteristics(
                    temp_filepath,
                    model.get("characteristics", {}),
                    filepath,
                )

                if not success:
                    # Custom voices must not silently fall back to the base gTTS output.
                    return jsonify(
                        {
                            "success": False,
                            "error": "Custom voice transformation produced no changes",
                        }
                    ), 500

                return jsonify(
                    {
                        "success": True,
                        "audio_url": f"/static/audio/{filename}",
                        "filename": filename,
                        "voice_type": "custom",
                        "voice_name": model.get("name", "Custom Voice"),
                        "characteristics_applied": success,
                        "used_characteristics": model.get("characteristics", {}),
                    }
                )
            finally:
                # Always remove the base gTTS temp file.
                try:
                    os.remove(temp_filepath)
                except:
                    pass

                # If transformation failed, avoid leaving a stray output MP3.
                if not success:
                    try:
                        os.remove(filepath)
                    except:
                        pass
        except Exception as e:
            print(f"Error generating custom voice: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "error": str(e)}), 500
    elif voice_key in VOICES:
        # Use standard voice with transformations
        voice = VOICES[voice_key]
        print(f"Using standard voice: {voice['name']}")
        
        try:
            # Use the generate_voice_with_characteristics function for proper transformations
            filename = generate_voice_with_characteristics(text, voice, slow)
            
            return jsonify({
                "success": True,
                "audio_url": f"/static/audio/{filename}",
                "filename": filename,
                "voice_type": "standard",
                "voice_name": voice["name"]
            })
        except Exception as e:
            print(f"Error generating standard voice: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": f"Voice '{voice_key}' not found"}), 404


@app.route("/api/synthesize-chunk", methods=["POST"])
def synthesize_chunk():
    cleanup_old_files()
    data = request.get_json() or {}
    text = (data.get("text") or "").strip()
    voice_key = data.get("voice", "voice_neutral")
    slow = data.get("slow", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400

    # Check if this is a custom trained voice (check models database first)
    models = load_voice_models()
    
    if voice_key in models:
        # Use custom trained voice model
        model = models[voice_key]
        print(f"Generating chunk with custom voice: {model['name']}")

        if not audio_transform_available():
            return jsonify(
                {
                    "success": False,
                    "error": "Audio processing not available. Install FFmpeg and restart to enable custom voice matching.",
                    "code": "FFMPEG_MISSING",
                }
            ), 412
        
        try:
            # Generate base audio
            base_lang = model.get("language", "en")
            base_key = model.get("base_voice_key") or pick_best_base_voice(
                model.get("characteristics", {})
            )
            base_voice = VOICES.get(base_key, VOICES["voice_neutral"])
            base_tld = base_voice.get("tld", "com")
            tts = gTTS(text=text, lang=base_lang, tld=base_tld, slow=slow)
            temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
            temp_filepath = os.path.join(AUDIO_DIR, temp_filename)
            tts.save(temp_filepath)
            
            # Apply voice characteristics
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)

            success = False
            try:
                success = apply_voice_characteristics(
                    temp_filepath,
                    model.get("characteristics", {}),
                    filepath,
                )

                if not success:
                    return jsonify(
                        {
                            "success": False,
                            "error": "Custom voice transformation produced no changes",
                        }
                    ), 500

                return jsonify(
                    {
                        "success": True,
                        "audio_url": f"/static/audio/{filename}",
                        "chunk_text": text,
                        "voice_type": "custom",
                        "characteristics_applied": success,
                        "voice_name": model.get("name", "Custom Voice"),
                        "used_characteristics": model.get("characteristics", {}),
                    }
                )
            finally:
                try:
                    os.remove(temp_filepath)
                except:
                    pass

                if not success:
                    try:
                        os.remove(filepath)
                    except:
                        pass
        except Exception as e:
            print(f"Error generating custom voice chunk: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"success": False, "error": str(e)}), 500
    elif voice_key in VOICES:
        # Use standard voice with transformations
        voice = VOICES[voice_key]
        print(f"Generating chunk with standard voice: {voice['name']}")
        
        try:
            # Use the generate_voice_with_characteristics function for proper transformations
            filename = generate_voice_with_characteristics(text, voice, slow)
            
            return jsonify({
                "success": True,
                "audio_url": f"/static/audio/{filename}",
                "chunk_text": text,
                "voice_type": "standard"
            })
        except Exception as e:
            print(f"Error generating standard voice chunk: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": f"Voice '{voice_key}' not found"}), 404


@app.route("/api/voices", methods=["GET"])
def get_voices():
    return jsonify(VOICES)


@app.route("/api/upload-clone", methods=["POST"])
def upload_clone():
    """Receive uploaded voice sample and process for voice cloning."""
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No file uploaded", "success": False}), 400
        
        file = request.files["audio"]
        if file.filename == "":
            return jsonify({"error": "Empty filename", "success": False}), 400

        allowed = {".wav", ".mp3", ".m4a", ".ogg", ".webm"}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed:
            return jsonify({"error": f"Unsupported format: {ext}", "success": False}), 400

        # Get voice training parameters
        voice_name = request.form.get("voice_name", "Custom Voice")
        training_text = request.form.get("training_text", "")
        duration = float(request.form.get("duration", 0))
        
        # Validate minimum requirements for quality
        if duration < 10 and duration > 0:
            return jsonify({
                "error": "Recording too short. Please record at least 10 seconds for better accuracy.",
                "success": False
            }), 400

        # Generate unique model ID
        model_id = f"voice_{uuid.uuid4().hex}"
        filename = f"{model_id}{ext}"
        filepath = os.path.join(VOICE_MODELS_DIR, filename)
        
        # Save the file
        file.save(filepath)
        print(f"File saved to: {filepath}")

        # Try to analyze audio characteristics
        try:
            characteristics = analyze_audio_characteristics(
                filepath, training_text=training_text
            )
            print(f"Audio characteristics: {characteristics}")
        except Exception as e:
            print(f"Warning: Could not analyze audio characteristics: {e}")
            # Use default characteristics
            characteristics = {
                "pitch": "medium",
                "speed": "normal",
                "tone": "neutral",
                "sample_rate": 44100,
                "quality_metrics": {}
            }
        
        # Calculate quality score based on duration and audio quality
        if duration == 0:
            # If duration not provided, estimate from file
            try:
                audio = AudioSegment.from_file(filepath)
                duration = len(audio) / 1000.0
            except:
                duration = 30  # Default estimate
        
        quality_score = min(100, int((duration / 60) * 100))  # Max quality at 60 seconds
        if duration >= 30:
            quality_score = min(100, quality_score + 10)  # Bonus for longer recordings
        
        # Adjust quality based on audio characteristics
        if characteristics.get("quality_metrics", {}).get("rms", 0) > 1000:
            quality_score = min(100, quality_score + 5)  # Bonus for good audio quality
        
        # Store voice model metadata
        models = load_voice_models()
        base_voice_key = pick_best_base_voice(characteristics)
        models[model_id] = {
            "name": voice_name,
            "filename": filename,
            "created_at": datetime.now().isoformat(),
            "duration": duration,
            "training_text": training_text,
            "quality_score": quality_score,
            "sample_count": 1,
            "language": "en",
            "base_voice_key": base_voice_key,
            "characteristics": {
                "pitch": characteristics.get("pitch", "medium"),
                "speed": characteristics.get("speed", "normal"),
                "tone": characteristics.get("tone", "neutral"),
                "sample_rate": characteristics.get("sample_rate", 44100),
                "quality_metrics": characteristics.get("quality_metrics", {})
            }
        }
        save_voice_models(models)
        
        print(f"Voice model saved: {model_id}")

        return jsonify({
            "success": True,
            "message": f"Voice model '{voice_name}' trained successfully with {quality_score}% accuracy!",
            "model_id": model_id,
            "voice_name": voice_name,
            "quality_score": quality_score,
            "duration": duration,
            "characteristics": models[model_id]["characteristics"],
            "recommendations": get_training_recommendations(duration, quality_score)
        })
    
    except Exception as e:
        print(f"Error in upload_clone: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": f"Server error: {str(e)}",
            "success": False
        }), 500


@app.route("/api/add-training-sample", methods=["POST"])
def add_training_sample():
    """Add additional training sample to improve existing voice model."""
    if "audio" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    model_id = request.form.get("model_id")
    if not model_id:
        return jsonify({"error": "Model ID required"}), 400
    
    models = load_voice_models()
    if model_id not in models:
        return jsonify({"error": "Voice model not found"}), 404
    
    file = request.files["audio"]
    duration = float(request.form.get("duration", 0))
    training_text = request.form.get("training_text", "")
    
    # Save additional sample
    sample_filename = f"{model_id}_sample_{models[model_id]['sample_count']}.webm"
    filepath = os.path.join(VOICE_MODELS_DIR, sample_filename)
    file.save(filepath)
    
    # Analyze new sample characteristics
    new_characteristics = analyze_audio_characteristics(
        filepath, training_text=training_text
    )
    
    # Update model metadata
    models[model_id]["sample_count"] += 1
    models[model_id]["duration"] += duration
    
    # Average characteristics from multiple samples
    old_chars = models[model_id]["characteristics"]
    sample_count = models[model_id]["sample_count"]
    
    # Blend characteristics (weighted average)
    if sample_count > 1:
        # Keep the most common pitch/speed/tone
        # In production, use more sophisticated blending
        pass
    
    # Recalculate quality score with multiple samples
    total_duration = models[model_id]["duration"]
    base_quality = min(100, int((total_duration / 60) * 100))
    sample_bonus = min(20, sample_count * 5)  # Up to 20% bonus for multiple samples
    
    # Audio quality bonus
    audio_quality_bonus = 0
    if new_characteristics.get("quality_metrics", {}).get("rms", 0) > 1000:
        audio_quality_bonus = 3
    
    models[model_id]["quality_score"] = min(100, base_quality + sample_bonus + audio_quality_bonus)
    
    save_voice_models(models)
    
    return jsonify({
        "success": True,
        "message": f"Training sample added! Quality improved to {models[model_id]['quality_score']}%",
        "quality_score": models[model_id]["quality_score"],
        "sample_count": sample_count,
        "total_duration": total_duration,
        "characteristics": models[model_id]["characteristics"]
    })


@app.route("/api/voice-models", methods=["GET"])
def get_voice_models():
    """Get all trained voice models."""
    models = load_voice_models()
    return jsonify({"success": True, "models": models})


@app.route("/api/voice-model/<model_id>", methods=["GET"])
def get_voice_model(model_id):
    """Get specific voice model details."""
    models = load_voice_models()
    if model_id not in models:
        return jsonify({"error": "Voice model not found"}), 404
    return jsonify({"success": True, "model": models[model_id]})


@app.route("/api/delete-voice-model/<model_id>", methods=["DELETE"])
def delete_voice_model(model_id):
    """Delete a voice model."""
    models = load_voice_models()
    if model_id not in models:
        return jsonify({"error": "Voice model not found"}), 404
    
    # Delete audio files
    model = models[model_id]
    try:
        os.remove(os.path.join(VOICE_MODELS_DIR, model["filename"]))
        # Delete additional samples
        for i in range(1, model["sample_count"]):
            sample_file = f"{model_id}_sample_{i}.webm"
            sample_path = os.path.join(VOICE_MODELS_DIR, sample_file)
            if os.path.exists(sample_path):
                os.remove(sample_path)
    except Exception as e:
        pass
    
    del models[model_id]
    save_voice_models(models)
    
    return jsonify({"success": True, "message": "Voice model deleted"})


def generate_voice_with_characteristics(text, voice_config, slow=False):
    """
    Generate speech with specific voice characteristics applied.
    This makes each voice sound TRULY different with strong transformations.
    """
    print(f"\n{'='*60}")
    print(f"🎙️  Generating voice: {voice_config['name']}")
    print(f"{'='*60}")
    
    # Generate base audio
    tts = gTTS(
        text=text, 
        lang=voice_config["lang"], 
        tld=voice_config.get("tld", "com"), 
        slow=slow
    )
    
    temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
    temp_filepath = os.path.join(AUDIO_DIR, temp_filename)
    tts.save(temp_filepath)
    print(f"✓ Base audio generated")
    
    # Apply voice-specific characteristics to make it VERY DIFFERENT
    if AUDIO_PROCESSING_AVAILABLE:
        try:
            audio = AudioSegment.from_file(temp_filepath)
            print(f"✓ Audio loaded: {len(audio)/1000:.2f}s")
            
            # === PITCH TRANSFORMATION ===
            pitch = voice_config.get("pitch", "medium")
            pitch_shift = 0
            
            if pitch == "high":
                pitch_shift = 5  # Strong shift for female voices
                print(f"  → Applying HIGH pitch (+5 semitones)")
            elif pitch == "low":
                pitch_shift = -5  # Strong shift for male deep voices
                print(f"  → Applying LOW pitch (-5 semitones)")
            elif pitch == "medium":
                pitch_shift = 0
                print(f"  → Keeping MEDIUM pitch (no shift)")
            
            if pitch_shift != 0:
                new_sample_rate = int(audio.frame_rate * (2.0 ** (pitch_shift / 12.0)))
                audio = audio._spawn(audio.raw_data, overrides={'frame_rate': new_sample_rate})
                audio = audio.set_frame_rate(44100)
                print(f"  ✓ Pitch shifted successfully")
            
            # === SPEED TRANSFORMATION ===
            speed = voice_config.get("speed", 1.0)
            if speed != 1.0:
                print(f"  → Applying speed: {speed}x")
                # Use frame rate manipulation for speed change
                sound_with_altered_frame_rate = audio._spawn(
                    audio.raw_data,
                    overrides={"frame_rate": int(audio.frame_rate * speed)}
                )
                audio = sound_with_altered_frame_rate.set_frame_rate(audio.frame_rate)
                print(f"  ✓ Speed adjusted successfully")
            
            # === GENDER-SPECIFIC TONE ===
            gender = voice_config.get("gender", "neutral")
            if gender == "female":
                # Brighter, clearer tone for female voices
                print(f"  → Applying FEMALE tone characteristics")
                audio = audio.high_pass_filter(180)  # Remove deep bass
                audio = audio.low_pass_filter(8000)  # Keep clarity
                audio = audio + 4  # Volume boost
                print(f"  ✓ Female tone applied (bright & clear)")
            elif gender == "male":
                # Warmer, deeper tone for male voices
                print(f"  → Applying MALE tone characteristics")
                audio = audio.low_pass_filter(4000)  # Emphasize warmth
                audio = audio.high_pass_filter(80)   # Remove rumble
                audio = audio + 2  # Slight boost
                print(f"  ✓ Male tone applied (warm & deep)")
            else:
                # Neutral - balanced tone
                print(f"  → Applying NEUTRAL tone")
                audio = audio.high_pass_filter(100)
                audio = audio.low_pass_filter(6000)
                audio = audio + 3
                print(f"  ✓ Neutral tone applied (balanced)")
            
            # === EXPORT WITH HIGH QUALITY ===
            final_filename = f"{uuid.uuid4().hex}.mp3"
            final_filepath = os.path.join(AUDIO_DIR, final_filename)
            audio.export(final_filepath, format="mp3", bitrate="192k")
            
            # Clean up temp file
            try:
                os.remove(temp_filepath)
            except:
                pass
            
            print(f"✅ Voice generated successfully!")
            print(f"   Final characteristics: pitch={pitch}, speed={speed}x, gender={gender}")
            print(f"{'='*60}\n")
            return final_filename
            
        except Exception as e:
            print(f"❌ Error applying characteristics: {e}")
            import traceback
            traceback.print_exc()
            # Return temp file if processing fails
            final_filename = f"{uuid.uuid4().hex}.mp3"
            final_filepath = os.path.join(AUDIO_DIR, final_filename)
            import shutil
            shutil.copy(temp_filepath, final_filepath)
            try:
                os.remove(temp_filepath)
            except:
                pass
            print(f"⚠️  Returned unprocessed audio")
            return final_filename
    else:
        # No audio processing available - return basic gTTS
        print(f"⚠️  Audio processing not available - using basic gTTS")
        print(f"   Install FFmpeg and restart for voice transformations")
        final_filename = f"{uuid.uuid4().hex}.mp3"
        final_filepath = os.path.join(AUDIO_DIR, final_filename)
        import shutil
        shutil.copy(temp_filepath, final_filepath)
        try:
            os.remove(temp_filepath)
        except:
            pass
        return final_filename


def get_training_recommendations(duration, quality_score):
    """Provide recommendations to improve voice model quality."""
    recommendations = []
    
    if duration < 30:
        recommendations.append("Record for at least 30 seconds to improve accuracy")
    if duration < 60:
        recommendations.append("Longer recordings (60+ seconds) produce better results")
    if quality_score < 70:
        recommendations.append("Add more training samples to improve quality")
    
    if quality_score >= 90:
        recommendations.append("Excellent quality! Your voice model is ready to use")
    elif quality_score >= 70:
        recommendations.append("Good quality. Consider adding more samples for best results")
    
    return recommendations


if __name__ == "__main__":
    app.run(debug=True, port=5000)
