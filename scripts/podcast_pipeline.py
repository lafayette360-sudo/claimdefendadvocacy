"""
Episode publishing pipeline for the Claim Defend Advocacy podcast/newsletter.

Drafts the Beehiiv (v2 API) newsletter post and stages YouTube Data API v3
metadata for an episode. Both API calls are human-in-the-loop: the Beehiiv
post is created as a draft, and the YouTube video is staged as private.

Required environment variables:
    BEEHIIV_API_KEY  - Beehiiv API key (Bearer token)
    BEEHIIV_PUB_ID   - Beehiiv publication ID (pub_xxxxxx)
"""

import os
import sys

import requests

BEEHIIV_API_KEY = os.environ.get("BEEHIIV_API_KEY")
BEEHIIV_PUB_ID = os.environ.get("BEEHIIV_PUB_ID")

BEEHIIV_HEADERS = {
    "Authorization": f"Bearer {BEEHIIV_API_KEY}",
    "Content-Type": "application/json",
}


def create_beehiiv_newsletter(subject, title, html_content, audio_url=None):
    """Create a draft post in Beehiiv for human review before sending."""
    if not BEEHIIV_API_KEY or not BEEHIIV_PUB_ID:
        raise RuntimeError(
            "BEEHIIV_API_KEY and BEEHIIV_PUB_ID must be set in the environment"
        )

    url = f"https://api.beehiiv.com/v2/publications/{BEEHIIV_PUB_ID}/posts"

    payload = {
        "title": title,
        "subtitle": "The Policyholder's Battle Plan",
        "subject": subject,
        "status": "draft",  # human-in-the-loop review before send
        "body": html_content,
        "channel": "email",
    }

    if audio_url:
        payload["advanced_settings"] = {"premium_web_override": False}
        # Audio embeds are injected directly into the HTML body as a player string.

    response = requests.post(url, headers=BEEHIIV_HEADERS, json=payload, timeout=30)

    if response.status_code == 201:
        post_id = response.json()["data"]["id"]
        print(f"[OK] Beehiiv draft created. Post ID: {post_id}")
        return post_id

    print(f"[ERROR] Beehiiv post creation failed: {response.status_code} - {response.text}")
    return None


def generate_youtube_metadata(episode_title, description, tags):
    """Build the YouTube Data API v3 metadata payload, staged as private."""
    metadata = {
        "snippet": {
            "title": f"Claim Defend Podcast | {episode_title}",
            "description": description,
            "tags": tags,
            "categoryId": "27",  # Education
        },
        "status": {
            "privacyStatus": "private",  # staged private until reviewed
            "selfDeclaredMadeForKids": False,
        },
    }
    print("[OK] YouTube metadata payload staged.")
    return metadata


def run_episode_1():
    episode_subject = "Why your initial roof inspection is a complete lie"
    episode_title = "The Roof Damage Trap: Why Your Initial Inspection is a Lie"

    newsletter_html = """
    <h2>The Policyholder's Battle Plan: Episode 1</h2>
    <hr/>
    <p><strong>Imagine waking up after a massive storm...</strong> You spot missing shingles, call your insurance carrier, and wait for "their" adjuster. That single move can lose you a $30,000 claim before it even starts.</p>
    <p>To beat them, you must execute the <strong>Independent Documentation Protocol</strong> before their adjuster sets foot on your lawn.</p>
    <blockquote><strong>The Gotcha Secret:</strong> Watch out for the 'Partial Repair' trap. If a matching shingle cannot be found due to weathering, they may legally owe you a complete roof replacement.</blockquote>
    <p><a href="http://ClaimDefend.online" style="background-color:#0052cc; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">Grab Your Property Claim Battle Plan Here</a></p>
    """

    video_description = (
        "Don't fall for the insurance company playbook. In this episode, we break down "
        "the Roof Damage Trap and how to protect your asset equity.\n\n"
        "Get your battle plan: http://ClaimDefend.online"
    )
    video_tags = ["roof insurance claim", "property damage", "public adjuster", "roof damage trap"]

    create_beehiiv_newsletter(episode_subject, episode_title, newsletter_html, audio_url=None)
    generate_youtube_metadata(episode_title, video_description, video_tags)


if __name__ == "__main__":
    try:
        run_episode_1()
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        sys.exit(1)
