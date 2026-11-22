import json
import random
from pathlib import Path

# High-converting viral hooks for Reels
VIRAL_HOOKS = [
    "Bro thought he could get away with this 💀",
    "Wait until the end... I wasn't expecting that 😭",
    "No way this actually happened in game 🤯",
    "Is this the craziest moment yet? Rate it 1-10 👇",
    "Tell me you play GTA without telling me you play GTA 😂",
    "The ending had me questioning everything 💀",
    "Send this to that one teammate who always sells the mission 😭",
    "Rockstar really outdid themselves with this one 🔥",
    "100% calculated or pure luck? You decide 👇",
    "How did he even survive this?! 💀🔥",
    "Never letting him drive the getaway car again 😂🚗",
    "NPCs in this game are on a whole different level 😭",
    "Bro tried to look cool and failed instantly 💀",
    "When the heist plan goes completely wrong 🤦‍♂️🔥",
    "GTA 6 physics better be exactly like this 😂",
    "This is why you don't trust randoms on missions 💀",
    "Bro activated god mode for 5 seconds ⚡",
    "The most chaotic 60 seconds you'll watch today 😭",
    "I still can't believe this worked out in the end 🤯",
    "Top 1% gaming moment right here 🏆🔥",
]

# High-engagement Calls to Action (CTAs)
ENGAGEMENT_CTAS = [
    "Follow @gta6chronicles3 for daily clips & highlights! 🔥",
    "Tag a friend who needs to see this! 😂",
    "Drop your honest rating in the comments (1-10) 👇",
    "Save this clip for later so you don't lose it! 💾",
    "Follow @gta6chronicles3 for the best daily gaming moments! 🚀",
    "Share this with your squad before GTA 6 drops! 🔥",
    "What would you have done here? Comment below! 💬",
    "Tag that one friend who always does this 💀",
    "Hit follow for Part 2! 🎯",
]

# Themed hashtag clusters for natural rotation
HASHTAG_CLUSTERS = {
    "gta_core": [
        "#gta6", "#gta", "#gtav", "#gta5", "#gtaclips", 
        "#rockstargames", "#grandtheftauto", "#gtaonline", 
        "#gta6hype", "#gtavicecity"
    ],
    "viral_explore": [
        "#reels", "#viral", "#trending", "#explorepage", 
        "#fyp", "#reelsinstagram", "#viralreels", "#foryou"
    ],
    "gaming_humor": [
        "#gaming", "#gamer", "#gamers", "#gamingmemes", 
        "#gameplay", "#videogames", "#twitchclips", "#funnygaming", 
        "#gamingcommunity", "#pcgaming", "#ps5"
    ]
}


class CaptionGenerator:
    def __init__(self, history_file: Path = None):
        self.history_file = history_file or (Path(__file__).resolve().parent / "logs" / "caption_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history = self._load_history()

    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"used_hooks": []}

    def _save_history(self):
        try:
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=2)
        except Exception:
            pass

    def get_diverse_hashtags(self, total_tags=12):
        """Pick a balanced, randomized mix of tags from each cluster."""
        selected = []
        # 4-5 from core GTA
        selected.extend(random.sample(HASHTAG_CLUSTERS["gta_core"], min(4, len(HASHTAG_CLUSTERS["gta_core"]))))
        # 4 from viral/explore
        selected.extend(random.sample(HASHTAG_CLUSTERS["viral_explore"], min(4, len(HASHTAG_CLUSTERS["viral_explore"]))))
        # 4 from gaming community
        selected.extend(random.sample(HASHTAG_CLUSTERS["gaming_humor"], min(4, len(HASHTAG_CLUSTERS["gaming_humor"]))))
        
        random.shuffle(selected)
        return " ".join(selected[:total_tags])

    def generate_metadata(self, custom_account="@gta6chronicles3") -> dict:
        """Generate structured metadata suitable for both Instagram Reels and YouTube Shorts."""
        recent_hooks = self.history.get("used_hooks", [])
        available_hooks = [h for h in VIRAL_HOOKS if h not in recent_hooks]
        
        if not available_hooks:
            available_hooks = VIRAL_HOOKS
            recent_hooks = []

        hook = random.choice(available_hooks)
        cta = random.choice(ENGAGEMENT_CTAS)
        if custom_account and "@gta6chronicles3" in cta:
            cta = cta.replace("@gta6chronicles3", custom_account)

        tags = self.get_diverse_hashtags()

        # Update and prune history (keep last 12 to ensure diversity)
        recent_hooks.append(hook)
        if len(recent_hooks) > 12:
            recent_hooks = recent_hooks[-12:]
        self.history["used_hooks"] = recent_hooks
        self._save_history()

        instagram_caption = f"{hook}\n\n{cta}\n.\n.\n.\n{tags}"

        # YouTube Shorts title (max 100 chars, append #Shorts)
        base_title = hook.strip()
        if len(base_title) > 85:
            base_title = base_title[:82].rstrip() + "..."
        yt_title = f"{base_title} #Shorts"
        
        yt_desc = f"{hook}\n\n{cta}\n\nSubscribe for daily highlights! 🔥\n\n{tags}\n\n#Shorts"

        clean_tags = [t.lstrip("#") for t in tags.split() if t.startswith("#")]

        return {
            "hook": hook,
            "cta": cta,
            "instagram_caption": instagram_caption,
            "youtube_title": yt_title,
            "youtube_description": yt_desc,
            "tags": clean_tags,
        }

    def generate(self, custom_account="@gta6chronicles3"):
        """Generate a fresh, unique viral caption with smart rotation."""
        return self.generate_metadata(custom_account=custom_account)["instagram_caption"]


_generator = None

def get_viral_caption(custom_account="@gta6chronicles3") -> str:
    """Convenience helper to generate a viral caption for Instagram Reels."""
    global _generator
    if _generator is None:
        _generator = CaptionGenerator()
    return _generator.generate(custom_account=custom_account)

def get_viral_metadata(custom_account="@gta6chronicles3") -> dict:
    """Convenience helper to generate coordinated metadata for Reels & YouTube Shorts."""
    global _generator
    if _generator is None:
        _generator = CaptionGenerator()
    return _generator.generate_metadata(custom_account=custom_account)
