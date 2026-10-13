import os, requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

AGNES_BASE = "https://apihub.agnes-ai.com"
AGNES_KEY = os.environ.get("AGNES_API_KEY", "")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate():
    prompt = request.form.get("prompt", "").strip()
    duration = request.form.get("duration", "5")
    if not prompt:
        return jsonify({"error": "Prompt likho"}), 400
    num_frames = 121 if duration == "5" else 241
    try:
        resp = requests.post(
            f"{AGNES_BASE}/v1/videos",
            headers={"Authorization": f"Bearer {AGNES_KEY}", "Content-Type": "application/json"},
            json={
                "model": "agnes-video-v2.0",
                "prompt": prompt,
                "height": 768,
                "width": 1152,
                "num_frames": num_frames,
                "frame_rate": 24
            },
            timeout=60
        )
        data = resp.json()
        video_id = data.get("video_id") or data.get("id") or data.get("task_id")
        if not video_id:
            return jsonify({"error": f"Task fail: {str(data)[:250]}"}), 500
        return jsonify({"job_id": video_id})
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)[:200]}"}), 500

@app.route("/status/<job_id>")
def status(job_id):
    try:
        resp = requests.get(
            f"{AGNES_BASE}/agnesapi",
            params={"video_id": job_id, "model_name": "agnes-video-v2.0"},
            headers={"Authorization": f"Bearer {AGNES_KEY}"},
            timeout=30
        )
        data = resp.json()
        st = data.get("status", "")
        if st in ["completed", "succeeded", "done"]:
            url = data.get("url") or data.get("video_url")
            return jsonify({"status": "done", "url": url})
        if st in ["failed", "error"]:
            return jsonify({"status": "failed", "error": data.get("message", "Failed")})
        return jsonify({"status": "processing", "raw": str(data)[:200]})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)[:200]}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, threaded=True)
