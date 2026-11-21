# Instagram Reels Auto-Uploader Bot

An automated Reels uploader built with `instagrapi` that safely schedules and posts videos from a local queue.

---

## Directory Overview

- `queue/`: Drop your `.mp4` video clips here.
- `posted/`: Successfully published videos are automatically archived here.
- `config.json`: Change scheduled times, jitter window, and default hashtags.
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
It will prompt for your username, password, and 2FA code (if enabled). Once verified, your session is saved to `session.json`.

*(Alternatively, you can create a `.env` file from `.env.example` with `IG_USERNAME` and `IG_PASSWORD`.)*

### 2. Add Videos to Queue
Copy any `.mp4` files into the `queue/` folder:
```bash
cp /path/to/my_clip.mp4 ~/instagram_reels_bot/queue/
```
*(Optional: You can create a companion `.txt` file with the exact same name, e.g. `my_clip.txt`, to provide a custom caption and hashtags for that specific clip.)*

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
