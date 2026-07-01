# VidCore Stream Extractor

A Flask web app that resolves streaming URLs from VidCore, deployable on Render.

## Deploy to Render (free)

1. Push this folder to a GitHub repo
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Render auto-detects `render.yaml` — click **Deploy**

That's it. Your app will be live at `https://your-app.onrender.com`.

## Run locally

```bash
pip install -r requirements.txt
python app.py
# Visit http://localhost:5000
```

## Usage

- Select **TV Series** or **Movie**
- Enter a **TMDB ID** (e.g. `1399` for Game of Thrones)
- For TV, enter season and episode numbers
- Click **Extract Streams** — results appear below with copy buttons

## API

`POST /api/fetch`

```json
{
  "type": "tv",
  "tmdb_id": "1399",
  "season": "1",
  "episode": "1"
}
```

Returns an array of server results with decrypted stream data.
