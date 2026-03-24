# Advanced Voice Training System

## Overview
The system now includes sophisticated audio analysis for highly accurate voice profiling and replication.

## Advanced Analysis Features

### 1. Pitch Detection (Fundamental Frequency)
- **Method**: Autocorrelation + FFT analysis
- **Range**: 50Hz - 500Hz
- **Accuracy**: ±5Hz
- **Output**: Exact fundamental frequency + category (low/medium/high)

**Typical Ranges:**
- Low (Male): 85-140Hz
- Medium: 140-200Hz  
- High (Female): 200-300Hz

### 2. Formant Analysis
- **Method**: FFT peak detection
- **Formants Detected**: F1, F2, F3
- **Purpose**: Characterizes voice timbre and quality

**Typical Formants:**
- F1: 700Hz (vowel openness)
- F2: 1220Hz (vowel frontness)
- F3: 2600Hz (voice quality)

### 3. Speech Rate Detection
- **Method**: Energy envelope analysis
- **Unit**: Syllables per second
- **Categories**:
  - Slow: <2.5 syll/s
  - Normal: 2.5-4.0 syll/s
  - Fast: >4.0 syll/s

### 4. Spectral Analysis
- **Spectral Centroid**: Center of mass of frequency spectrum
- **Purpose**: Determines tone quality (warm/neutral/bright)
- **Range**: 200-3000Hz

### 5. Quality Metrics
- **SNR**: Signal-to-Noise Ratio estimate
- **ZCR**: Zero Crossing Rate (voice clarity)
- **Dynamic Range**: Volume variation
- **Spectral Flatness**: Noisiness measure

## Installation

```bash
pip install scipy
```

## Usage

The advanced analysis runs automatically when you upload/record voice samples.

## Output Example

```
============================================================
🔬 ADVANCED VOICE ANALYSIS
============================================================
Analyzing: voice_abc123.mp3

📊 Basic Properties:
  Duration: 45.23s
  Sample Rate: 44100Hz
  Channels: 1

🔊 Amplitude Analysis:
  RMS: 0.3456
  Average: 0.2789
  Peak: 0.9876

🎵 Pitch Analysis:
  Fundamental Frequency: 142.50Hz
  Category: LOW

🎼 Formant Analysis:
  F1: 720.45Hz
  F2: 1250.30Hz
  F3: 2680.15Hz

⚡ Speech Rate Analysis:
  Rate: 3.45 syllables/second
  Category: NORMAL

🎨 Spectral Analysis:
  Spectral Centroid: 950.25Hz
  Tone: WARM

✨ Quality Metrics:
  SNR Estimate: 25.30dB
  Zero Crossing Rate: 0.0456
  Dynamic Range: 22.15dB

============================================================
✅ ANALYSIS COMPLETE
============================================================
```

## Benefits

1. **Higher Accuracy**: Precise voice characteristic detection
2. **Better Matching**: More accurate voice replication
3. **Quality Assessment**: Automatic quality scoring
4. **Detailed Profiling**: Complete voice fingerprint

## Technical Details

### Algorithms Used:
- **Autocorrelation**: Pitch detection
- **FFT**: Frequency analysis
- **Peak Detection**: Formant identification
- **Energy Envelope**: Speech rate
- **Spectral Analysis**: Tone quality

### Processing Pipeline:
1. Load audio → Normalize
2. Pitch detection → Fundamental frequency
3. FFT analysis → Formants
4. Energy analysis → Speech rate
5. Spectral analysis → Tone
6. Quality metrics → SNR, ZCR, etc.

## Troubleshooting

**"Advanced analysis unavailable"**
- Install scipy: `pip install scipy`
- Restart the application

**Analysis takes too long**
- Normal for files >60 seconds
- Consider shorter samples for faster processing

**Inaccurate results**
- Ensure quiet recording environment
- Use good quality microphone
- Record clear speech (not whispering)

## Next Steps

After training with advanced analysis:
1. Check quality score (aim for 90%+)
2. Verify detected characteristics match your voice
3. Add multiple samples for best results
4. Generate speech and compare
