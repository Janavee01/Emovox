def generate_emotional_audio(story: str, progress_queue=None, output_path="final_story_with_bgm.wav") -> dict:
    import os, time
    import nltk
    from pydub import AudioSegment
    from nltk.tokenize import sent_tokenize
    from collections import Counter
    import requests

    def report(stage, msg):
        if progress_queue:
            progress_queue.put({"stage": stage, "message": msg})
        print(f"[{stage}] {msg}")

    # Ensure NLTK tokenizer is available
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    # Emotion classifier (local)
    from transformers import pipeline
    report("init", "🤖 Loading emotion classifier...")
    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=1,
        device=-1
    )

    # Hugging Face API
    HF_TOKEN = os.environ.get("HF_TOKEN")
    if not HF_TOKEN:
        raise RuntimeError("HF_TOKEN environment variable not set")

    API_URL_TINYLLAMA = "https://api-inference.huggingface.co/models/TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    API_URL_PARLER = "https://api-inference.huggingface.co/models/parler-tts/parler-tts-mini-expresso"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}

    # Generate voice prompt using TinyLlama API
    def generate_voice_prompt(sentence, emotion):
        prompt = f"""### Instruction:
You are a voice direction assistant. Given a sentence and its dominant emotion, write a one-sentence, natural-sounding vocal delivery style for a female narrator.

### Sentence:
"{sentence}"

### Emotion:
{emotion}

### Voice direction:"""
        response = requests.post(API_URL_TINYLLAMA, headers=headers, json={"inputs": prompt})
        result_text = response.json()[0]["generated_text"]
        return f"A calm woman narrates {result_text.split('### Voice direction:')[-1].strip()}: '{sentence}'"

    # Generate Parler-TTS audio using API
    def generate_parler_audio(voice_prompt):
        response = requests.post(API_URL_PARLER, headers=headers, json={"inputs": voice_prompt})
        temp_file = "temp.wav"
        with open(temp_file, "wb") as f:
            f.write(response.content)
        return temp_file

    # Load background music per emotion
    def load_emotion_bgm(emotion, length_ms, music_dir="bg/"):
        path = os.path.join(music_dir, f"{emotion}.mp3")
        if not os.path.exists(path):
            path = os.path.join(music_dir, "neutral.mp3")
        if os.path.exists(path):
            bgm = AudioSegment.from_file(path)
            return (bgm * ((length_ms // len(bgm)) + 1))[:length_ms].fade_in(1000).fade_out(1000).apply_gain(-14)
        return AudioSegment.silent(duration=length_ms)

    # Tokenize story & detect emotions
    report("emotion", "📝 Tokenizing story and detecting emotions...")
    sentences = sent_tokenize(story)
    emotion_results = emotion_classifier(sentences)
    emotions = [res[0]['label'].lower() for res in emotion_results]
    dominant_emotion = Counter(emotions).most_common(1)[0][0]
    report("emotion", f"💭 Detected dominant emotion: {dominant_emotion}")

    # Generate audio for each sentence
    output_audio = AudioSegment.silent(duration=0)
    emotion_pause = {"joy": 300, "sadness": 600, "anger": 200, "fear": 500, "surprise": 400, "love": 350, "neutral": 300}

    for i, sentence in enumerate(sentences):
        detected_emotion = emotions[i]
        report("tts", f"🎙️ Generating audio for sentence {i+1}/{len(sentences)} ({detected_emotion})")
        try:
            voice_prompt = generate_voice_prompt(sentence, detected_emotion)
            temp_wav = generate_parler_audio(voice_prompt)
            segment = AudioSegment.from_wav(temp_wav)
            os.remove(temp_wav)

            pause_duration = emotion_pause.get(detected_emotion, 300)
            output_audio += segment + AudioSegment.silent(duration=pause_duration)

        except Exception as e:
            report("error", f"❌ Error on sentence {i+1}: {e}")
            continue

    # Export voice-only audio
    report("mixing", "🎵 Exporting voice-only audio...")
    voice_only_path = output_path.replace(".wav", "_voice.wav")
    output_audio.export(voice_only_path, format="wav")

    # Add background music
    report("mixing", f"🎶 Adding {dominant_emotion} background music...")
    bgm = load_emotion_bgm(dominant_emotion, len(output_audio))
    final_mix = (bgm + 1).overlay(output_audio - 1)
    final_mix.export(output_path, format="wav")

    report("done", "✅ Processing complete")

    return {
        "audio_path": output_path,
        "dominant_emotion": dominant_emotion,
        "num_sentences": len(sentences),
        "emotions": emotions,
        "sentences": sentences
    }
