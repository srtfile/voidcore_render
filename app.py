import re
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

HEADERS_BASE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    "Referer": "https://vidcore.net/",
    "X-Requested-With": "XMLHttpRequest"
}
API = "https://enc-dec.app/api"


def validate(data, path):
    if data.get("status") != 200:
        raise ValueError(f"API error at {path}: {data.get('error', 'unknown')} (status {data.get('status')})")
    return data["result"]


def fetch_streams(media_type, tmdb_id, season=None, episode=None):
    if media_type == "movie":
        base_url = f"https://vidcore.net/movie/{tmdb_id}/"
    else:
        base_url = f"https://vidcore.net/tv/{tmdb_id}/{season}/{episode}/"

    response = requests.get(base_url, timeout=15).text
    match = re.search(r'\\"en\\":\\"(.*?)\\"', response)
    if not match:
        raise ValueError("Could not extract text token from page. The TMDB ID may be invalid.")
    text = match.group(1)

    enc_vidcore = f"{API}/enc-vidcore?text={text}"
    resp = requests.get(enc_vidcore, timeout=15).json()
    parts = validate(resp, enc_vidcore)

    servers_url = parts['servers']
    stream_base = parts['stream']
    token = parts['token']

    headers = {**HEADERS_BASE, "X-CSRF-Token": token}

    servers_encrypted = requests.post(servers_url, headers=headers, timeout=15).text
    dec_resp = requests.post(f"{API}/dec-vidcore", json={"text": servers_encrypted}, timeout=15).json()
    servers_decrypted = validate(dec_resp, f"{API}/dec-vidcore")

    results = []
    for server in servers_decrypted:
        data_val = server.get('data')
        server_name = server.get('name', 'Unknown')
        if not data_val:
            continue
        try:
            stream_url = f"{stream_base}/{data_val}"
            stream_enc = requests.post(stream_url, headers=headers, timeout=15).text
            stream_resp = requests.post(f"{API}/dec-vidcore", json={"text": stream_enc}, timeout=15).json()
            stream_data = validate(stream_resp, f"{API}/dec-vidcore")
            results.append({
                "server": server_name,
                "data": stream_data,
                "referer": HEADERS_BASE["Referer"]
            })
        except Exception as e:
            results.append({
                "server": server_name,
                "error": str(e)
            })

    return results


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    body = request.json or {}
    media_type = body.get("type", "tv")
    tmdb_id = body.get("tmdb_id", "").strip()
    season = body.get("season", "1")
    episode = body.get("episode", "1")

    if not tmdb_id:
        return jsonify({"error": "TMDB ID is required"}), 400

    try:
        results = fetch_streams(media_type, tmdb_id, season, episode)
        return jsonify({"success": True, "results": results})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=False)
