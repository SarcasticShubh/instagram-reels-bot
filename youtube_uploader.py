import os
import sys
import json
import logging
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "uploader.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("youtube_uploader")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

DEFAULT_CLIENT_SECRET = BASE_DIR / "client_secret.json"
DEFAULT_TOKEN_FILE = BASE_DIR / "youtube_token.json"


def get_authenticated_service(client_secret_path: Path = None, token_path: Path = None, run_flow_if_missing: bool = False):
    """Obtain or refresh Google YouTube API v3 service."""
    client_secret_path = client_secret_path or DEFAULT_CLIENT_SECRET
    token_path = token_path or DEFAULT_TOKEN_FILE

    creds = None
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        except Exception as e:
            logger.warning(f"Could not load existing token from {token_path}: {e}")

    if creds and creds.expired and creds.refresh_token:
        try:
            logger.info("Refreshing expired YouTube OAuth access token...")
            creds.refresh(Request())
            with open(token_path, "w", encoding="utf-8") as f:
                f.write(creds.to_json())
            logger.info("YouTube token refreshed successfully.")
        except Exception as e:
            logger.warning(f"Failed to refresh YouTube token: {e}")
            creds = None

    if not creds or not creds.valid:
        if not run_flow_if_missing:
            return None

        if not client_secret_path.exists():
            logger.error(
                f"Missing '{client_secret_path.name}'! "
                "Download OAuth 2.0 Client credentials from Google Cloud Console and place it here."
            )
            return None

        logger.info("Starting Google OAuth 2.0 authorization flow...")
        flow = InstalledAppFlow.from_client_secrets_file(str(client_secret_path), SCOPES)
        try:
            creds = flow.run_local_server(port=0, open_browser=True)
        except Exception:
            logger.info("Could not launch browser automatically. Printing URL...")
            creds = flow.run_local_server(port=0, open_browser=False)

        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
        logger.info(f"YouTube OAuth credentials saved to {token_path.name}!")

    return build("youtube", "v3", credentials=creds)


def is_youtube_authenticated(client_secret_path: Path = None, token_path: Path = None) -> bool:
    """Check if valid credentials or refreshable tokens are present."""
    token_path = token_path or DEFAULT_TOKEN_FILE
    if not token_path.exists():
        return False
    try:
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        return bool(creds and (creds.valid or creds.refresh_token))
    except Exception:
        return False


def get_channel_info(service=None) -> dict:
    """Retrieve basic channel info for the authenticated user."""
    service = service or get_authenticated_service(run_flow_if_missing=False)
    if not service:
        return {}
    try:
        response = service.channels().list(part="snippet,statistics", mine=True).execute()
        items = response.get("items", [])
        if items:
            snippet = items[0].get("snippet", {})
            stats = items[0].get("statistics", {})
            return {
                "id": items[0].get("id"),
                "title": snippet.get("title"),
                "customUrl": snippet.get("customUrl", ""),
                "subscribers": stats.get("subscriberCount", "0"),
                "videoCount": stats.get("videoCount", "0"),
            }
    except Exception as e:
        logger.warning(f"Failed to fetch YouTube channel info: {e}")
    return {}


def upload_youtube_short(
    video_path: Path,
    title: str,
    description: str,
    tags: list = None,
    category_id: str = "20",
    privacy_status: str = "public",
    client_secret_path: Path = None,
    token_path: Path = None,
) -> dict:
    """Upload a video to YouTube formatted as a Short."""
    service = get_authenticated_service(
        client_secret_path=client_secret_path,
        token_path=token_path,
        run_flow_if_missing=False,
    )
    if not service:
        raise RuntimeError(
            "YouTube service is not authenticated. "
            "Please run: ./run.sh yt-login to authorize."
        )

    # Ensure #Shorts is present in title and description
    clean_title = title.strip()
    if "#Shorts" not in clean_title and "#shorts" not in clean_title:
        clean_title = f"{clean_title} #Shorts"

    # YouTube title hard limit is 100 characters
    if len(clean_title) > 100:
        clean_title = clean_title[:92].rstrip() + "... #Shorts"

    clean_desc = description.strip()
    if "#Shorts" not in clean_desc and "#shorts" not in clean_desc:
        clean_desc = f"{clean_desc}\n\n#Shorts"

    tag_list = ["Shorts", "Short"] + (tags or [])
    # Filter duplicate tags while preserving order
    seen = set()
    deduped_tags = []
    for t in tag_list:
        clean_t = t.lstrip("#").strip()
        if clean_t.lower() not in seen:
            seen.add(clean_t.lower())
            deduped_tags.append(clean_t)

    body = {
        "snippet": {
            "title": clean_title,
            "description": clean_desc,
            "tags": deduped_tags[:25],
            "categoryId": str(category_id),
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        },
    }

    logger.info(f"Uploading YouTube Short: '{clean_title}' ({privacy_status})")
    media = MediaFileUpload(
        str(video_path),
        chunksize=4 * 1024 * 1024,  # 4MB chunks
        resumable=True,
        mimetype="video/mp4",
    )

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    last_reported = -1
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            if pct != last_reported and pct % 20 == 0:
                logger.info(f"YouTube upload progress: {pct}%")
                last_reported = pct

    video_id = response.get("id")
    short_url = f"https://youtube.com/shorts/{video_id}"
    logger.info(f"SUCCESS! YouTube Short published: {short_url}")

    return {
        "id": video_id,
        "url": short_url,
        "title": clean_title,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="YouTube Shorts Uploader CLI")
    parser.add_argument("--auth", action="store_true", help="Run interactive Google OAuth flow")
    parser.add_argument("--status", action="store_true", help="Check YouTube authorization status")
    parser.add_argument("--upload", type=str, help="Upload a video file as YouTube Short")
    parser.add_argument("--title", type=str, default="Viral Gaming Moment #Shorts", help="Video title")
    parser.add_argument("--desc", type=str, default="Daily gaming clips! Subscribe for more.", help="Video description")
    parser.add_argument("--privacy", type=str, default="public", choices=["public", "unlisted", "private"])

    args = parser.parse_args()

    if args.auth:
        svc = get_authenticated_service(run_flow_if_missing=True)
        if svc:
            info = get_channel_info(svc)
            print("\nAuthorization Successful!")
            if info:
                print(f"Connected Channel: {info.get('title')} ({info.get('customUrl')})")
        else:
            print("\nAuthorization failed. Please ensure 'client_secret.json' exists.")
            sys.exit(1)

    elif args.status or len(sys.argv) == 1:
        if is_youtube_authenticated():
            info = get_channel_info()
            print("\nYouTube Status: AUTHENTICATED")
            if info:
                print(f"Channel Name  : {info.get('title')}")
                print(f"Subscribers   : {info.get('subscribers')}")
                print(f"Total Videos  : {info.get('videoCount')}")
            else:
                print("Could not retrieve channel info (quota or permissions issue).")
        else:
            print("\nYouTube Status: NOT AUTHENTICATED")
            if not DEFAULT_CLIENT_SECRET.exists():
                print(f"Notice: '{DEFAULT_CLIENT_SECRET.name}' not found.")
                print("Please create an OAuth Client ID in Google Cloud Console and place 'client_secret.json' in this folder.")
            else:
                print("Client secret found. Run: python youtube_uploader.py --auth to log in.")

    elif args.upload:
        video_file = Path(args.upload)
        if not video_file.exists():
            print(f"Error: Video file not found: {video_file}")
            sys.exit(1)
        res = upload_youtube_short(
            video_file,
            title=args.title,
            description=args.desc,
            privacy_status=args.privacy,
        )
        print(f"Published successfully: {res['url']}")
