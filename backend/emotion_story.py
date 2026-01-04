# emotion_story.py
import torch
import nltk
import gc
import os
from parler_tts import ParlerTTSForConditionalGeneration
from pydub import AudioSegment
from random import seed as set_seed
from nltk.tokenize import sent_tokenize
from collections import Counter
from transformers import (
    pipeline,
    AutoTokenizer
)
import numpy as np
from models import (
    emotion_classifier,
    llm_pipe,
    parler_model,
    parler_tokenizer,
    parler_device
)

def generate_emotional_audio(story: str, progress_queue=None, output_path="final_story_with_bgm.wav") -> dict:
    import os, gc, torch, nltk
    import soundfile as sf

    def report(stage, msg):
        if progress_queue:
            progress_queue.put({"stage": stage, "message": msg})
        print(f"[{stage}] {msg}")

    # Ensure NLTK tokenizer is available
    try:
        nltk.data.find("tokenizers/punkt")
    except LookupError:
        nltk.download("punkt")

    # Tokenize story
    sentences = sent_tokenize(story)  

    # Detect emotions
    report("emotion", "Detecting emotions for all sentences...")
    emotion_results = emotion_classifier(sentences)
    emotions = [res[0]['label'].lower() for res in emotion_results]
    dominant_emotion = Counter(emotions).most_common(1)[0][0]
    report("emotion", f"Dominant emotion: {dominant_emotion}")

    
    # Generate all voice prompts in batch
    report("tts", "Generating voice directions for all sentences...")
    voice_prompts = []
    for i, sentence in enumerate(sentences):
        prompt = f"""### Instruction:
You are a voice direction assistant. Given a sentence and its dominant emotion, write a one-sentence, natural-sounding vocal delivery style for a female narrator describing exactly how her voice should express the emotion.

### Sentence:
"{sentence}"

### Emotion:
{emotions[i]}

### Voice direction:"""
        result = llm_pipe(prompt, max_new_tokens=60, temperature=0.7, do_sample=True)
        direction = result[0]['generated_text'].split('### Voice direction:')[-1].strip()
        voice_prompts.append(f"A calm woman narrates {direction}: '{sentence}'")

    # Generate audio in **batch** to speed things up
    output_audio = AudioSegment.empty()
    emotion_pause = {
        "joy": 300, "sadness": 600, "anger": 200,
        "fear": 500, "surprise": 400, "love": 350, "neutral": 300
    }

    report("tts", "🎶 Generating TTS audio for all sentences (batch)...")
    input_ids_list = [parler_tokenizer(vp, return_tensors="pt").input_ids.to(parler_device)
                      for vp in voice_prompts]
    prompt_ids_list = [parler_tokenizer(s, return_tensors="pt").input_ids.to(parler_device)
                       for s in sentences]

    for i, (input_ids, prompt_ids) in enumerate(zip(input_ids_list, prompt_ids_list)):
        try:
            set_seed(42 + i)
            audio_tensor = parler_model.generate(
            input_ids=input_ids,
            prompt_input_ids=prompt_ids,
            do_sample=True,
            top_p=0.85,
            temperature=0.95,
            max_new_tokens=800
        )

           
            audio_np = audio_tensor.cpu().numpy().squeeze()
            audio_int16 = np.int16(audio_np * 32767)
            segment = AudioSegment(
                audio_int16.tobytes(),
                frame_rate=parler_model.config.sampling_rate,
                sample_width=2,  # int16 is 2 bytes
                channels=1
            )

            pause_duration = emotion_pause.get(emotions[i], 300)
            output_audio += segment + AudioSegment.silent(duration=pause_duration)

            del input_ids, prompt_ids, audio_tensor
            torch.cuda.empty_cache()
            gc.collect()
            report("tts", f"Finished sentence {i+1}/{len(sentences)}")
        except Exception as e:
            report("error", f"Error generating sentence {i+1}: {e}")
            continue

    # Export voice-only audio
    voice_only_path = output_path.replace(".wav", "_voice.wav")
    report("mixing", f"🎵 Exporting voice-only audio to {voice_only_path}...")
    output_audio.export(voice_only_path, format="wav")

    # Load background music
    def load_emotion_bgm(emotion, length_ms):
        try:
            music_dir = os.path.join(os.path.dirname(__file__), "bg")
            path = os.path.join(music_dir, f"{emotion}.mp3")

            if not os.path.exists(path):
                path = os.path.join(music_dir, "neutral.mp3")

            if not os.path.exists(path):
                return AudioSegment.silent(duration=length_ms)

            bgm = AudioSegment.from_file(path)
            return (
                bgm * ((length_ms // len(bgm)) + 1)
            )[:length_ms].fade_in(1000).fade_out(1000).apply_gain(-14)

        except Exception as e:
            report("warning", f"BGM skipped: {e}")
            return AudioSegment.silent(duration=length_ms)


    report("mixing", f"🎶 Adding {dominant_emotion} background music...")
    bgm = load_emotion_bgm(dominant_emotion, len(output_audio))
    final_mix = (bgm + 1).overlay(output_audio - 1)
    final_mix.export(output_path, format="wav")

    report("done", "Processing complete")

    return {
        "audio_path": output_path,
        "dominant_emotion": dominant_emotion,
        "num_sentences": len(sentences),
        "emotions": emotions,
        "sentences": sentences
    }
