# Instagram Reels Auto-Uploader Bot

An automated Reels uploader built with `instagrapi` that safely schedules and posts videos from a local queue.

---

## Key Features

- **⚡ Automated Scheduling:** Posts up to 4 reels per day across peak engagement windows with randomized human jitter (±10 min).
- **🔥 Dynamic Viral Captions:** Automatically rotates engaging hooks, call-to-actions, and hashtag clusters so no two reels share the exact same caption or tags.
- **🛡️ Anti-Spam Tag Balancing:** Draws from themed hashtag pools (Core GTA, Viral/Explore, Gaming Community) to avoid Instagram's repeated-hashtag penalty.
- **💾 Session Persistence:** Safely caches authenticated session cookies in `session.json`—no re-logging required.
- **📁 Smart Queue & Archiving:** Automatically moves published clips from `queue/` to `posted/`.

---

## Directory Overview

- `caption_generator.py`: Smart engine that generates diverse viral hooks, CTAs, and tag combinations.
- `queue/`: Drop your `.mp4` video clips here.
- `posted/`: Successfully published videos are automatically archived here.
- `config.json`: Change scheduled times, jitter window, account handle, and paths.
- `session.json`: Stores your authenticated session cookies safely.
- `logs/uploader.log`: Detailed execution log.

---

## Quick Start

### 1. Perform Initial Login (One-time)
Run the login command in your terminal:
```bash
cd ~/instagram_reels_bot
./run.sh login
```
*(Or authenticate using your web browser cookie via `./run.sh sessionid "YOUR_SESSION_ID"`).*

### 2. Add Videos to Queue
Copy any `.mp4` files into the `queue/` folder:
```bash
cp /path/to/my_clip.mp4 ~/instagram_reels_bot/queue/
```
*(Optional: If you want a specific custom caption for `my_clip.mp4`, drop a text file named `my_clip.txt` next to it. Otherwise, the bot will auto-generate a fresh viral caption and tags).*

### 3. Test a Single Upload
To test publishing immediately without waiting for the schedule:
```bash
./run.sh post-now
```

### 4. Check Queue & Status
```bash
./run.sh status
```

### 5. Start the Continuous Scheduler (4 Reels / day)
```bash
./run.sh start
```
To stop the background bot:
```bash
./run.sh stop
```
To monitor live logs:
```bash
tail -f logs/uploader.log
```
