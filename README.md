# Multi-Platform Reels & Shorts Auto-Uploader Bot

An automated publisher for **Instagram Reels** and **YouTube Shorts** that safely schedules and cross-posts videos from a local queue.

---

## Key Features

- **⚡ Multi-Platform Cross-Posting:** Publishes simultaneously to **Instagram Reels** and **YouTube Shorts** (platforms can be toggled independently in `config.json`).
- **🔥 Dynamic Viral Captions & Titles:** Automatically generates engaging hooks, calls-to-action, and hashtag clusters for Instagram, plus punchy `<100` char `#Shorts` titles and descriptions for YouTube.
- **🛡️ Anti-Repetition & Anti-Spam Memory:** Tracks recently used hooks in `logs/caption_history.json` to prevent consecutive repetition, and rotates hashtags across multiple clusters.
- **💾 Dual Session Persistence:** 
  - Instagram: Session cookies cached in `session.json`.
  - YouTube: Official Google OAuth 2.0 with auto-refreshing tokens stored in `youtube_token.json`.
- **📁 Queue & Auto-Archiving:** Drops videos in `queue/` and archives published clips in `posted/`.

---

## Directory Overview

- `uploader.py`: Main cross-platform scheduler and publisher.
- `youtube_uploader.py`: YouTube Data API v3 uploader and OAuth manager.
- `caption_generator.py`: Smart caption, title, and hashtag rotation engine.
- `queue/`: Drop your `.mp4` video clips here.
- `posted/`: Successfully published videos are automatically archived here.
- `config.json`: Platform toggles, scheduled times, jitter window, and paths.
- `run.sh`: Convenient command runner for status, logins, and background service.

---

## Setup & Quick Start

### 1. Instagram Setup (One-time)
Authenticate using your web browser cookie:
```bash
./run.sh sessionid "YOUR_SESSION_ID"
```

### 2. YouTube Shorts Setup (One-time)
1. Go to [Google Cloud Console](https://console.cloud.google.com/) and create a project.
2. Enable the **YouTube Data API v3**.
3. Under **APIs & Services > Credentials**, create **OAuth 2.0 Client ID** (select **Desktop App**).
4. Download the JSON file, rename it to `client_secret.json`, and place it in this directory (`~/instagram_reels_bot/client_secret.json`).
5. Run the one-time authorization:
```bash
./run.sh yt-login
```
*(Your browser will open to log in with your YouTube Google account and grant upload permissions. Subsequent uploads refresh automatically).*

---

### 3. Add Videos to Queue
Copy any `.mp4` video files into `queue/`:
```bash
cp /path/to/my_clip.mp4 ~/instagram_reels_bot/queue/
```
*(Optional: If you want a specific custom caption for `my_clip.mp4`, drop a text file named `my_clip.txt` next to it).*

---

### 4. Commands Reference

| Command | Description |
| :--- | :--- |
| `./run.sh status` | Check queue count and connection status for both platforms |
| `./run.sh post-now` | Publish the next queued video immediately to active platforms |
| `./run.sh yt-login` | Authenticate with YouTube (Google OAuth) |
| `./run.sh yt-status` | View YouTube channel name, subscriber count, and video count |
| `./run.sh start` | Start the background scheduler (4 posts/day) |
| `./run.sh stop` | Stop the background scheduler |
| `tail -f logs/uploader.log` | View live execution logs |
