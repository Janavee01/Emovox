# backend/models.py
import torch
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
from parler_tts import ParlerTTSForConditionalGeneration

print("🔁 Loading models once...")

# Emotion classifier
emotion_classifier = pipeline(
    "text-classification",
    model="j-hartmann/emotion-english-distilroberta-base",
    top_k=1,
    device=-1
)

# TinyLlama
LLM_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
llm_tokenizer = AutoTokenizer.from_pretrained(LLM_ID)
llm_model = AutoModelForCausalLM.from_pretrained(LLM_ID).to("cpu")
llm_pipe = pipeline(
    "text-generation",
    model=llm_model,
    tokenizer=llm_tokenizer,
    device=-1
)

# Parler-TTS
parler_device = "cuda" if torch.cuda.is_available() else "cpu"
parler_model = ParlerTTSForConditionalGeneration.from_pretrained(
    "parler-tts/parler-tts-mini-expresso",
    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
).to(parler_device)

parler_tokenizer = AutoTokenizer.from_pretrained(
    "parler-tts/parler-tts-mini-expresso"
)

print("Models ready")
