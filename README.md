# 🎙️ Emovox — Emotion-Aware Storyteller

**Emovox** is a full-stack generative AI application that transforms short written stories into emotionally expressive audio. It uses state-of-the-art NLP and TTS models to detect sentence-level emotions and generate matching vocal narration. To make the speech sound more human and emotionally appropriate, Emovox uses a lightweight language model (TinyLlama) to generate natural-sounding voice direction prompts, guiding how each sentence should be spoken by the TTS system. The final audio is further enhanced with adaptive background music that aligns with the overall emotional tone of the story.

---

## 🔧 Features

- 🎭 **Emotion Detection**: Identifies dominant emotion for each sentence using a fine-tuned DistilRoBERTa model.
- 🗣️ **Voice Direction Generation**: Uses TinyLlama to craft natural-sounding voice prompts tailored to each emotion.
- 🔊 **Expressive TTS**: Synthesizes sentence-wise audio with Parler-TTS and merges it seamlessly.
- 🎼 **Adaptive Music Scoring**: Mixes background music that matches the overall emotion of the story.
- 📊 **Emotional Timeline**: Visualizes the emotion flow sentence-by-sentence using Chart.js.
- 🌐 **Web Interface**: React frontend with real-time progress updates and audio playback.

---

## 🛠️ Tech Stack

| Layer        | Technology Used                                           |
|--------------|------------------------------------------------------------|
| Frontend     | React, Chart.js, Tailwind CSS                              |
| Backend      | Flask, Flask-CORS                                          |
| AI Models    | Transformers (DistilRoBERTa, TinyLlama), Parler-TTS        |
| Audio Tools  | PyDub, SoundFile                                           |
| Others       | NLTK, Torch                                                |

---

## 📦 Installation

### 🔹 Backend Setup (Python)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Janavee01/Emovox.git
   cd Emovox
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Navigate to backend/ folder and run the flask server**
   ```bash
   python app.py
   ```

###  🔹 Frontend Setup (React)
#### Open a new terminal and navigate to the frontend/ folder 

1. **Install required packages:**
   ```bash
    npm install
    npm install chart.js react-chartjs-2
   ```

2. **Start the React app**
   ```bash
    npm start/ npm run dev(if vite is used)
   ```

# 🎧 Emotional Audio Generator

Transform short stories into immersive, emotion-rich audio experiences using AI-driven voice synthesis and sound design.

---

## 🧪 **How It Works**

### **Input**
- User provides or selects a short story via the frontend.

### **Processing Pipeline**

1. **Sentence Segmentation**
   - The story is split into individual sentences.

2. **Emotion Detection**
   - Each sentence is analyzed for its emotional tone.

3. **Voice Direction Generation**
   - Voice acting instructions are created using TinyLlama based on emotional context.

4. **Expressive Speech Synthesis**
   - Parler-TTS generates expressive audio clips per sentence.

5. **Audio Stitching**
   - Synthesized clips are stitched with emotion-aware pauses.

6. **Background Music Mixing**
   - Emotion-specific music is layered under the narration.

7. **Final Output**
   - A `.wav` or `.mp3` file is returned to the frontend for playback.

8. **Emotion Timeline Visualization**
   - A graph is generated showing sentence-level emotions over time.

---
---

## 📁 **Project Structure**

```bash
Emovox/
├── app.py                  # Flask backend entry point
├── emotion_story.py        # Core logic for TTS, emotion detection, and mixing
├── requirements.txt        # Python dependencies
├── outputs/                # Generated audio files
├── bg/                     # Background music files by emotion
├── frontend/               # React app (optional location)
└── README.md
```

---

## 🧠 **Models Used**

- [`j-hartmann/emotion-english-distilroberta-base`](https://huggingface.co/j-hartmann/emotion-english-distilroberta-base)  
  *Sentence-level emotion classification using DistilRoBERTa.*

- [`TinyLlama/TinyLlama-1.1B-Chat-v1.0`](https://huggingface.co/TinyLlama/TinyLlama-1.1B-Chat-v1.0)  
  *Generates expressive voice direction prompts for synthesized speech.*

- [`parler-tts/parler-tts-mini-expresso`](https://huggingface.co/parler-tts/parler-tts-mini-expresso)  
  *Creates high-quality, emotionally nuanced audio clips.*

---
