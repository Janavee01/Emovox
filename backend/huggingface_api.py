import requests
import uuid
import os

HF_TOKEN = os.getenv("HF_TOKEN")  # Make sure you export this on EC2
TINY_LLAMA_MODEL = "your-username/tiny-llama"
PARLER_TTS_MODEL = "your-username/parler-tts"

def generate_prompt_with_tinylama(prompt_text):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": prompt_text, "parameters": {"max_new_tokens": 50}}

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{TINY_LLAMA_MODEL}",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        output = response.json()
        return output[0]['generated_text']  # API may vary
    else:
        raise Exception(f"TinyLLaMA API error: {response.text}")


def generate_speech(text):
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {"inputs": text}

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{PARLER_TTS_MODEL}",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        audio_bytes = response.content
        os.makedirs("outputs", exist_ok=True)
        output_path = f"outputs/{uuid.uuid4()}.wav"
        with open(output_path, "wb") as f:
            f.write(audio_bytes)
        return output_path
    else:
        raise Exception(f"Parler TTS API error: {response.text}")
