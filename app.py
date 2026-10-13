import os, time, requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

AGNES_API = "https://api.agnes-ai.com/v1/video/generations"
AGNES_KEY = os.environ.get("AGNES_API_KEY", "sk-free-demo-key")

JOBS = {}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "").strip()
    duration = request.form.get("duration", "5")
    if not prompt:
        return jsonify({"error": "Prompt likho"}), 400
    if duration not in ["5", "10"]:
        duration = "5"

    try:
        resp = requests.post(
            AGNES_API,
            headers={
                "Authorization": f"Bearer {AGNES_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "agnes-video-v2.0",
                "prompt": prompt,
                "duration": int(duration),
                "width": 1088,
                "height": 832,
                "fps": 24
            },
            timeout=30
        )
        data = resp.json()
        if "id" not in data and "task_id" not in data:
            return jsonify({"error": str(data)[:200]}), 500
        job_id = data.get("id") or data.get("task_id")
        JOBS[job_id] = {"status": "processing", "url": None}
        return jsonify({"job_id": job_id})
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)[:200]}"}), 500

@app.route("/status/<job_id>")
def status(job_id):
    try:
        resp = requests.get(
            f"{AGNES_API}/{job_id}",
            headers={"Authorization": f"Bearer {AGNES_KEY}"},
            timeout=20
        )
        data = resp.json()
        st = data.get("status", "processing")
        if st in ["succeeded", "completed", "done"]:
            url = data.get("url") or data.get("video_url") or data.get("output")
            return jsonify({"status": "done", "url": url})
        if st in ["failed", "error"]:
            return jsonify({"status": "failed", "error": data.get("error", "Failed")})
        return jsonify({"status": "processing"})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)[:200]}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
