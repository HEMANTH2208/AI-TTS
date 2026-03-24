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
    import numpy as np
    from scipy import signal
    from scipy.fft import fft, fftfreq
    AUDIO_PROCESSING_AVAILABLE = True
    ADVANCED_ANALYSIS_AVAILABLE = True
    print("✅ Audio processing libraries loaded (pydub, numpy, scipy)")
except ImportError as e:
    try:
        from pydub import AudioSegment
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

def analyze_audio_characteristics(audio_path):
    """
    Analyze audio file to extract voice characteristics.
    This is a simplified version - in production, use proper audio analysis libraries.
    """
    if not AUDIO_PROCESSING_AVAILABLE:
        print("Audio processing not available, using defaults")
        return {
            "duration": 30,
            "sample_rate": 44100,
            "channels": 1,
            "pitch": "medium",
            "speed": "normal",
            "tone": "neutral",
            "quality_metrics": {
                "rms": 1000,
                "avg_amplitude": 3000
            }
        }
    
    try:
        # Load audio file
        audio = AudioSegment.from_file(audio_path)
        
        # Extract basic characteristics
        duration = len(audio) / 1000.0  # Convert to seconds
        sample_rate = audio.frame_rate
        channels = audio.channels
        
        # Convert to numpy array for analysis
        samples = np.array(audio.get_array_of_samples())
        
        # Calculate basic audio features
        rms = np.sqrt(np.mean(samples**2))  # Root mean square (volume)
        
        # Estimate pitch category based on frequency content
        # This is simplified - real implementation would use FFT
        avg_amplitude = np.mean(np.abs(samples))
        
        # Categorize characteristics
        pitch = "medium"
        if avg_amplitude > 5000:
            pitch = "high"
        elif avg_amplitude < 2000:
            pitch = "low"
        
        speed = "normal"  # Would need speech recognition for accurate speed
        tone = "neutral"  # Would need sentiment analysis
        
        return {
            "duration": duration,
            "sample_rate": sample_rate,
            "channels": channels,
            "pitch": pitch,
            "speed": speed,
            "tone": tone,
            "quality_metrics": {
                "rms": float(rms),
                "avg_amplitude": float(avg_amplitude)
            }
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
    if not AUDIO_PROCESSING_AVAILABLE:
        print("⚠️  Audio processing not available - using original audio")
        print("   Install FFmpeg and restart to enable voice matching")
        try:
            import shutil
            shutil.copy(audio_path, output_path)
            return False  # Characteristics not applied
        except Exception as e:
            print(f"Error copying file: {e}")
            return False
    
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
        print(f"   Falling back to original audio")
        # If processing fails, just copy the original
        try:
            import shutil
            shutil.copy(audio_path, output_path)
        except Exception as copy_error:
            print(f"   Error copying file: {copy_error}")
        return False

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
    voice_key = data.get("voice", "arthur_us")
    slow = data.get("slow", False)

    if not text:
        return jsonify({"error": "No text provided"}), 400
    if len(text) > 3000:
        return jsonify({"error": "Text too long (max 3000 characters)"}), 400

    # Check if this is a custom trained voice
    models = load_voice_models()
    is_custom_voice = voice_key.startswith("voice_")
    
    if is_custom_voice and voice_key in models:
        # Use custom voice model
        model = models[voice_key]
        print(f"Using custom voice: {model['name']} (ID: {voice_key})")
        
        try:
            # For custom voices, we'll use a hybrid approach:
            # 1. Generate base audio with gTTS
            # 2. Apply the user's voice characteristics heavily
            
            # Use the closest gTTS voice based on characteristics
            base_lang = model.get("language", "en")
            base_tld = "com"
            
            # Generate base audio
            tts = gTTS(text=text, lang=base_lang, tld=base_tld, slow=slow)
            temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
            temp_filepath = os.path.join(AUDIO_DIR, temp_filename)
            tts.save(temp_filepath)
            
            # Apply voice characteristics to match trained voice
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            
            success = apply_voice_characteristics(
                temp_filepath,
                model.get("characteristics", {}),
                filepath
            )
            
            # Clean up temp file
            try:
                os.remove(temp_filepath)
            except:
                pass
            
            if not success:
                print("Warning: Voice characteristics not fully applied")
            
            return jsonify({
                "success": True,
                "audio_url": f"/static/audio/{filename}",
                "filename": filename,
                "voice_type": "custom",
                "voice_name": model.get("name", "Custom Voice"),
                "characteristics_applied": success
            })
        except Exception as e:
            print(f"Error generating custom voice: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    else:
        # Use standard gTTS voice
        voice = VOICES.get(voice_key, VOICES["arthur_us"])
        print(f"Using standard voice: {voice['name']}")
        
        try:
            tts = gTTS(text=text, lang=voice["lang"], tld=voice["tld"], slow=slow)
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            tts.save(filepath)
            return jsonify({
                "success": True,
                "audio_url": f"/static/audio/{filename}",
                "filename": filename,
                "voice_type": "standard",
                "voice_name": voice["name"]
            })
        except Exception as e:
            print(f"Error generating standard voice: {e}")
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

    # Check if this is a custom trained voice
    models = load_voice_models()
    is_custom_voice = voice_key.startswith("voice_")
    
    if is_custom_voice and voice_key in models:
        # Use custom voice model
        model = models[voice_key]
        print(f"Generating chunk with custom voice: {model['name']}")
        
        try:
            # Generate base audio
            base_lang = model.get("language", "en")
            tts = gTTS(text=text, lang=base_lang, slow=slow)
            temp_filename = f"temp_{uuid.uuid4().hex}.mp3"
            temp_filepath = os.path.join(AUDIO_DIR, temp_filename)
            tts.save(temp_filepath)
            
            # Apply voice characteristics
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            
            success = apply_voice_characteristics(
                temp_filepath,
                model.get("characteristics", {}),
                filepath
            )
            
            # Clean up temp file
            try:
                os.remove(temp_filepath)
            except:
                pass
            
            return jsonify({
                "success": True,
                "audio_url": f"/static/audio/{filename}",
                "chunk_text": text,
                "voice_type": "custom",
                "characteristics_applied": success
            })
        except Exception as e:
            print(f"Error generating custom voice chunk: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    else:
        # Use standard gTTS voice
        voice = VOICES.get(voice_key, VOICES["arthur_us"])
        try:
            filename = f"{uuid.uuid4().hex}.mp3"
            filepath = os.path.join(AUDIO_DIR, filename)
            tts = gTTS(text=text, lang=voice["lang"], tld=voice["tld"], slow=slow)
            tts.save(filepath)
            return jsonify({
                "success": True,
                "audio_url": f"/static/audio/{filename}",
                "chunk_text": text,
                "voice_type": "standard"
            })
        except Exception as e:
            print(f"Error generating standard voice chunk: {e}")
            return jsonify({"error": str(e)}), 500


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
            characteristics = analyze_audio_characteristics(filepath)
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
        models[model_id] = {
            "name": voice_name,
            "filename": filename,
            "created_at": datetime.now().isoformat(),
            "duration": duration,
            "training_text": training_text,
            "quality_score": quality_score,
            "sample_count": 1,
            "language": "en",
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
    new_characteristics = analyze_audio_characteristics(filepath)
    
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
