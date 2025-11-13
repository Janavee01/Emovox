def generate_emotional_audio(story: str, progress_queue=None, output_path="final_story_with_bgm.wav") -> dict:
    import os, time, nltk, torch, gc
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    from parler_tts import ParlerTTSForConditionalGeneration
    from pydub import AudioSegment
    import soundfile as sf
    from random import seed as set_seed
    from nltk.tokenize import sent_tokenize
    from collections import Counter

    def report(stage, msg):
        if progress_queue:
            progress_queue.put({"stage": stage, "message": msg})
        print(f"[{stage}] {msg}")

    # Ensure NLTK tokenizer is available
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    # Load emotion classifier
    report("init", "🤖 Loading emotion classifier...")
    emotion_classifier = pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=1,
        device=-1
    )

    # Load Parler-TTS and TinyLlama for voice direction
    report("init", "🎤 Loading Parler-TTS model...")
    parler_device = "cuda" if torch.cuda.is_available() else "cpu"
    parler_model = ParlerTTSForConditionalGeneration.from_pretrained(
        "parler-tts/parler-tts-mini-expresso",
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
    ).to(parler_device)
    parler_tokenizer = AutoTokenizer.from_pretrained("parler-tts/parler-tts-mini-expresso")

    report("init", "🧠 Loading TinyLlama for voice direction...")
    llm_model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
    llm_tokenizer = AutoTokenizer.from_pretrained(llm_model_id)
    llm_model = AutoModelForCausalLM.from_pretrained(llm_model_id).to("cpu")
    pipe = pipeline("text-generation", model=llm_model, tokenizer=llm_tokenizer, device=-1)

    def generate_voice_prompt(sentence, emotion):
        prompt = f"""### Instruction:
You are a voice direction assistant. Given a sentence and its dominant emotion, write a one-sentence, natural-sounding **vocal delivery style** for a *female narrator*, describing exactly how her voice should express the emotion.

### Sentence:
"{sentence}"

### Emotion:
{emotion}

### Voice direction:"""
        result = pipe(prompt, max_new_tokens=60, temperature=0.7, do_sample=True)
        return f"A calm woman narrates {result[0]['generated_text'].split('### Voice direction:')[-1].strip()}: '{sentence}'"

    def load_emotion_bgm(emotion, length_ms, music_dir="bg/"):
        path = f"{music_dir}/{emotion}.mp3"
        if not os.path.exists(path):
            path = f"{music_dir}/neutral.mp3"
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
    output_audio = AudioSegment.empty()
    emotion_pause = {
        "joy": 300, "sadness": 600, "anger": 200,
        "fear": 500, "surprise": 400, "love": 350, "neutral": 300
    }

    for i, sentence in enumerate(sentences):
        detected_emotion = emotions[i]
        report("tts", f"🎙️ Generating audio for sentence {i+1}/{len(sentences)}: '{sentence[:50]}...' ({detected_emotion})")
        try:
            voice_prompt = generate_voice_prompt(sentence, detected_emotion)
            input_ids = parler_tokenizer(voice_prompt, return_tensors="pt").input_ids.to(parler_device)
            prompt_ids = parler_tokenizer(sentence, return_tensors="pt").input_ids.to(parler_device)

            set_seed(42 + i)
            audio_tensor = parler_model.generate(
                input_ids=input_ids,
                prompt_input_ids=prompt_ids,
                do_sample=True,
                top_p=0.9,
                temperature=1.0
            )
            audio = audio_tensor.cpu().numpy().squeeze()

            temp_filename = f"sentence_{i}.wav"
            sf.write(temp_filename, audio, samplerate=parler_model.config.sampling_rate)
            segment = AudioSegment.from_wav(temp_filename)
            os.remove(temp_filename)

            pause_duration = emotion_pause.get(detected_emotion, 300)
            output_audio += segment + AudioSegment.silent(duration=pause_duration)

            del input_ids, prompt_ids, audio_tensor
            torch.cuda.empty_cache()
            gc.collect()

        except Exception as e:
            report("error", f"❌ Error on sentence {i+1}: {e}")
            continue

    # Export voice-only audio
    report("mixing", "🎵 Exporting voice-only audio...")
    voice_only_path = output_path.replace(".wav", "_voice.wav")
    output_audio.export(voice_only_path, format="wav")

    # Add background music
    report("mixing", f"🎶 Adding {dominant_emotion} background music...")
    bgm = load_emotion_bgm(dominant_emotion, length_ms=len(output_audio))
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
