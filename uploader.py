#!/usr/bin/env python3
import os
import sys
import json
import time
import random
import shutil
import subprocess
import logging
import argparse
from pathlib import Path
from datetime import datetime

import schedule
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired,
    ChallengeRequired,
    TwoFactorRequired,
    BadPassword,
)
from caption_generator import get_viral_caption

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
ENV_PATH = BASE_DIR / ".env"

# Load config
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    CONFIG = json.load(f)

QUEUE_DIR = BASE_DIR / CONFIG["paths"]["queue"]
POSTED_DIR = BASE_DIR / CONFIG["paths"]["posted"]
SESSION_PATH = BASE_DIR / CONFIG["paths"]["session"]
LOG_PATH = BASE_DIR / CONFIG["paths"]["log"]

LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
QUEUE_DIR.mkdir(parents=True, exist_ok=True)
POSTED_DIR.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("ReelsBot")


def load_env_credentials():
    """Load credentials from .env or OS environment."""
    username = os.environ.get("IG_USERNAME")
    password = os.environ.get("IG_PASSWORD")
    sessionid = os.environ.get("IG_SESSIONID")

    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k == "IG_USERNAME" and not username:
                        username = v
                    elif k == "IG_PASSWORD" and not password:
                        password = v
                    elif k == "IG_SESSIONID" and not sessionid:
                        sessionid = v
    return username, password, sessionid


def challenge_code_handler(username, choice):
    """Callback for Instagram security challenge / verification code."""
    print(f"\n[!] Instagram requested verification code for {username} via {choice}.")
    code = input("Enter the 6-digit code received: ").strip()
    return code


def login_with_sessionid(sessionid: str):
    """Log in directly using a web browser sessionid cookie."""
    cl = Client()
    cl.delay_range = [2, 5]
    logger.info("Authenticating via browser sessionid cookie...")
    try:
        cl.login_by_sessionid(sessionid)
        cl.dump_settings(SESSION_PATH)
        logger.info(f"Session successfully saved to {SESSION_PATH}!")
        return cl
    except Exception as e:
        logger.error(f"Failed to authenticate with sessionid: {e}")
        sys.exit(1)


def get_client(force_relogin=False):
    """Initialize client, loading saved session if available."""
    cl = Client()
    cl.challenge_code_handler = challenge_code_handler
    cl.delay_range = [2, 5]

    session_loaded = False
    if SESSION_PATH.exists() and not force_relogin:
        try:
            logger.info(f"Loading existing session from {SESSION_PATH}...")
            cl.load_settings(SESSION_PATH)
            if cl.user_id:
                session_loaded = True
                logger.info(f"Session verified successfully for user ID {cl.user_id}!")
        except Exception as e:
            logger.warning(f"Saved session error: {e}")
            session_loaded = False

    if not session_loaded:
        username, password, sessionid = load_env_credentials()
        if sessionid:
            return login_with_sessionid(sessionid)

        if not username or not password:
            print("\n--- Instagram Authentication Required ---")
            username = input("Instagram Username: ").strip()
            import getpass
            password = getpass.getpass("Instagram Password: ").strip()

        logger.info(f"Logging in as {username}...")
        try:
            cl.login(username, password)
            cl.dump_settings(SESSION_PATH)
            logger.info(f"Login successful! Session dumped to {SESSION_PATH}")
        except TwoFactorRequired:
            code = input("Enter your 2FA verification code: ").strip()
            cl.login(username, password, verification_code=code)
            cl.dump_settings(SESSION_PATH)
            logger.info(f"2FA Login successful! Session dumped to {SESSION_PATH}")
        except BadPassword:
            logger.error("Incorrect username or password.")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Login failed: {e}")
            sys.exit(1)

    return cl


def get_next_video():
    """Find the oldest video file in the queue."""
    video_extensions = {".mp4", ".mov", ".mkv"}
    videos = sorted(
        [p for p in QUEUE_DIR.iterdir() if p.is_file() and p.suffix.lower() in video_extensions],
        key=lambda p: p.stat().st_mtime,
    )
    if not videos:
        return None
    return videos[0]


def get_caption_for_video(video_path: Path):
    """Check if a matching .txt exists for custom caption, otherwise generate dynamic viral caption."""
    txt_path = video_path.with_suffix(".txt")
    if txt_path.exists():
        try:
            caption = txt_path.read_text(encoding="utf-8").strip()
            if caption:
                logger.info(f"Found custom caption file: {txt_path.name}")
                return caption
        except Exception as e:
            logger.warning(f"Failed to read custom caption from {txt_path}: {e}")

    # Generate a fresh viral hook + CTA + rotated tag set
    account_handle = CONFIG.get("account_handle", "@gta6chronicles3")
    try:
        caption = get_viral_caption(custom_account=account_handle)
        logger.info(f"Generated dynamic viral caption for {video_path.name}")
        return caption
    except Exception as e:
        logger.warning(f"Failed to generate dynamic caption, falling back to default: {e}")
        return CONFIG.get("default_caption", "Daily Reel 🔥 #reels #explore")


def post_next_reel(apply_jitter=False):
    """Pick video from queue and publish to Instagram Reels."""
    video_path = get_next_video()
    if not video_path:
        logger.info("Queue is empty. No video to post right now.")
        return False

    if apply_jitter:
        max_jitter = int(CONFIG.get("jitter_minutes", 10))
        if max_jitter > 0:
            delay_sec = random.randint(60, max_jitter * 60)
            logger.info(f"Applying random jitter: waiting {delay_sec // 60}m {delay_sec % 60}s before posting...")
            time.sleep(delay_sec)

    logger.info(f"Preparing to upload: {video_path.name}")
    caption = get_caption_for_video(video_path)

    # Pre-generate thumbnail using ffmpeg for instant, reliable processing
    thumb_path = video_path.with_suffix(".jpg")
    if not thumb_path.exists():
        logger.info(f"Generating thumbnail using ffmpeg for {video_path.name}...")
        subprocess.run([
            "ffmpeg", "-y", "-ss", "00:00:01", "-i", str(video_path),
            "-vframes", "1", "-q:v", "2", str(thumb_path)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        cl = get_client()
        logger.info("Uploading Reel...")
        media = cl.clip_upload(
            str(video_path),
            caption=caption,
            thumbnail=thumb_path if thumb_path.exists() else None,
        )
        logger.info(f"SUCCESS! Reel uploaded. Media ID: {media.pk} (Code: {media.code})")

        # Move video to posted folder
        dest_video = POSTED_DIR / video_path.name
        shutil.move(str(video_path), str(dest_video))
        logger.info(f"Moved {video_path.name} -> {POSTED_DIR.name}/")

        # Move companion files (txt, jpg) if present
        for ext in [".txt", ".jpg"]:
            extra_file = video_path.with_suffix(ext)
            if extra_file.exists():
                shutil.move(str(extra_file), str(POSTED_DIR / extra_file.name))

        # Refresh session dump
        cl.dump_settings(SESSION_PATH)
        return True

    except Exception as e:
        logger.error(f"Failed to upload reel {video_path.name}: {e}", exc_info=True)
        return False


def check_status():
    """Display queue count, archive count, and session status."""
    video_extensions = {".mp4", ".mov", ".mkv"}
    queued = [p.name for p in QUEUE_DIR.iterdir() if p.is_file() and p.suffix.lower() in video_extensions]
    posted = [p.name for p in POSTED_DIR.iterdir() if p.is_file() and p.suffix.lower() in video_extensions]

    print("\n===============================")
    print("   INSTAGRAM REELS BOT STATUS  ")
    print("===============================")
    print(f"Videos in queue : {len(queued)}")
    for name in queued[:5]:
        print(f"  • {name}")
    if len(queued) > 5:
        print(f"  ... and {len(queued) - 5} more")

    print(f"\nVideos posted   : {len(posted)}")
    print(f"Session saved   : {'Yes' if SESSION_PATH.exists() else 'No (Run --login first)'}")
    print(f"Schedule times  : {', '.join(CONFIG.get('schedule_times', []))}")
    print(f"Jitter window   : ±{CONFIG.get('jitter_minutes', 10)} min")
    print("===============================\n")


def run_scheduler():
    """Run persistent scheduler matching target times."""
    times = CONFIG.get("schedule_times", ["09:30", "13:15", "18:00", "21:30"])
    logger.info("Initializing Reels Scheduler...")
    logger.info(f"Scheduled daily posting times: {', '.join(times)}")

    # Pre-verify or create session
    get_client()

    for t in times:
        schedule.every().day.at(t).do(post_next_reel, apply_jitter=True)

    logger.info("Scheduler active. Waiting for next window (Press Ctrl+C to stop)...")
    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Automated Instagram Reels Bot")
    parser.add_argument("--login", action="store_true", help="Perform initial interactive login and save session")
    parser.add_argument("--sessionid", type=str, help="Authenticate using browser sessionid cookie")
    parser.add_argument("--post-now", action="store_true", help="Post the next queued video immediately")
    parser.add_argument("--run", action="store_true", help="Start continuous scheduled posting loop")
    parser.add_argument("--status", action="store_true", help="Show current bot status and queue counts")

    args = parser.parse_args()

    if args.sessionid:
        login_with_sessionid(args.sessionid)
    elif args.login:
        get_client(force_relogin=True)
    elif args.post_now:
        post_next_reel(apply_jitter=False)
    elif args.run:
        run_scheduler()
    elif args.status or len(sys.argv) == 1:
        check_status()


if __name__ == "__main__":
    main()
