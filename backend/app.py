from flask import Flask, request, jsonify, Response, send_file
from flask_cors import CORS
from threading import Thread
from queue import Queue
import time
import json
import os
import uuid

from emotion_story import generate_emotional_audio

app = Flask(__name__)
CORS(app)

user_queues = {}
audio_paths = {}
emotion_data = {}

@app.route("/api/emotions/<progress_id>")
def get_emotion_data(progress_id):
    data = emotion_data.get(progress_id)
    if not data:
        return jsonify({"error": "Emotion data not available"}), 404
    return jsonify(data)

@app.route("/api/story", methods=["POST"])
def story_to_audio():
    try:
        data = request.get_json()
        story = data.get("story", "").strip()
        if not story:
            return jsonify({"error": "No story provided"}), 400

        progress_id = str(uuid.uuid4())
        progress_queue = Queue()
        user_queues[progress_id] = progress_queue

        def background_task():
            try:
                os.makedirs("outputs", exist_ok=True)
                output_path = f"outputs/{progress_id}.wav"
                result = generate_emotional_audio(story, progress_queue, output_path=output_path)

                audio_path = result.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    audio_paths[progress_id] = audio_path
                    emotion_data[progress_id] = {
                        "emotions": result.get("emotions", []),
                        "sentences": result.get("sentences", [])
                    }
                else:
                    progress_queue.put({"stage": "error", "message": "Audio generation failed"})
            except Exception as e:
                progress_queue.put({"stage": "error", "message": f"Exception: {str(e)}"})
            finally:
                if progress_id not in audio_paths:
                    progress_queue.put({"stage": "error", "message": "❌ Processing terminated unexpectedly."})
                elif not any(item.get("stage") == "done" for item in list(progress_queue.queue)):
                    progress_queue.put({"stage": "done", "message": "✅ Processing complete"})

        Thread(target=background_task).start()
        return jsonify({"progress_id": progress_id})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/progress/<progress_id>")
def progress_stream(progress_id):
    def event_stream():
        q = user_queues.get(progress_id)
        if not q:
            yield "data: {\"stage\": \"error\", \"message\": \"Invalid progress ID\"}\n\n"
            return
        while True:
            update = q.get()
            print("Sending SSE update:", update)
            yield f"data: {json.dumps(update)}\n\n"
            time.sleep(0.01)
            if update.get("stage") in ("done", "error"):
                break
        user_queues.pop(progress_id, None)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/api/audio/<progress_id>")
def download_audio(progress_id):
    wav_path = audio_paths.get(progress_id)
    if not wav_path or not os.path.exists(wav_path):
        return jsonify({"error": "Audio not available"}), 404

    mp3_path = wav_path.replace(".wav", ".mp3")
    if os.path.exists(mp3_path):
        return send_file(mp3_path, mimetype="audio/mpeg", as_attachment=True, download_name="story.mp3")

    return send_file(wav_path, mimetype="audio/wav", as_attachment=True, download_name="story.wav")

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
