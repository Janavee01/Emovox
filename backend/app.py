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

# Store queues for each session by progress_id
user_queues = {}
audio_paths = {}

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
                result = generate_emotional_audio(story, progress_queue)
                audio_path = result.get("audio_path")
                if audio_path and os.path.exists(audio_path):
                    audio_paths[progress_id] = audio_path
                    # Do not send 'done' here if already sent by generate_emotional_audio
                    # progress_queue.put({"stage": "done", "message": "✅ Processing complete"})
                else:
                    progress_queue.put({"stage": "error", "message": "Audio generation failed"})
            except Exception as e:
                progress_queue.put({"stage": "error", "message": f"Exception: {str(e)}"})
            finally:
                # Ensure some form of final update is sent if not already
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
            print("Sending SSE update:", update)  # for debugging
            yield f"data: {json.dumps(update)}\n\n"
            time.sleep(0.01)  # helps flush buffer
            if update.get("stage") in ("done", "error"):
                break
        user_queues.pop(progress_id, None)

    return Response(event_stream(), mimetype="text/event-stream")

@app.route("/api/audio/<progress_id>")
def download_audio(progress_id):
    audio_path = audio_paths.get(progress_id)
    if not audio_path or not os.path.exists(audio_path):
        return jsonify({"error": "Audio not available"}), 404
    return send_file(audio_path, mimetype="audio/wav", as_attachment=True, download_name="story.wav")


# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
