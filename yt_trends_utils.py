# yt_trends_utils.py
from googleapiclient.discovery import build
#from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta
from pytrends.request import TrendReq





from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound, CouldNotRetrieveTranscript
import logging
from typing import List, Dict
from urllib.parse import urlparse



import os

YOUTUBE_API_KEY = "AIzaSyArcmO3SEp5xCHVOmgEBMDB6Zu4xTipICQ"  # or hardcode temporarily

logger = logging.getLogger(__name__)
def get_recent_video_captions(max_results=10):
    youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

    published_after = (datetime.utcnow() - timedelta(days=1)).isoformat("T") + "Z"
    query = "BSE|NSE|India|Jewar|stock"

    search_response = youtube.search().list(
        q=query,
        part="id,snippet",
        maxResults=max_results,
        publishedAfter=published_after,
        regionCode="IN",
        type="video",
        order="viewCount"  # 🔥 sort by most viewed
    ).execute()

    results = []

    for item in search_response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]

        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            captions = " ".join([seg["text"] for seg in transcript])
        except Exception as e:
            captions = f"Transcript not available: {e}"

        results.append({
            "title": title,
            "videoId": video_id,
            "captions": captions
        })

    return results



def get_google_trends_for_india():
    print("[INFO] Initializing pytrends...")
    pytrends = TrendReq(hl='en-IN', tz=330)

    try:
        print("[INFO] Trying pytrends.trending_searches()...")
        df = pytrends.trending_searches()
        if df.empty:
            print("[WARN] Empty result from trending_searches()")
            raise Exception("Empty trending data")

        trends = df[0].tolist()
        print(f"[INFO] Got {len(trends)} trends from global feed.")

        filter_keywords = ['india', 'nse', 'bse', 'rbi', 'modi', 'ipl', 'sensex', 'delhi', 'mumbai']
        filtered_trends = [kw for kw in trends if any(x in kw.lower() for x in filter_keywords)]

        print(f"[INFO] Filtered {len(filtered_trends)} India-related trends.")
        return filtered_trends or trends

    except Exception as e:
        print(f"[ERROR] Primary fetch failed: {e}")
        print("[INFO] Falling back to static India-related keywords.")

        fallback_trends = [
            "Lok Sabha Elections 2025",
            "India vs Pakistan",
            "Sensex",
            "NSE Live",
            "BSE News",
            "Modi Speech",
            "RBI Policy",
            "Delhi Rain",
            "IPL 2025",
            "JEE Advanced Results"
        ]
        return fallback_trends



def _extract_handle_from_input(channel_name: str) -> str:
    """
    Normalize input. Accepts:
      - '@handle'
      - 'kidomelon2682'
      - 'https://www.youtube.com/@kidomelon2682'
      - 'https://www.youtube.com/channel/UCxxxxx' (channel id)
    Returns a tuple (mode, value) where mode in {'channelId','handle'}
    """
    if not channel_name:
        return ("handle", "")

    channel_name = channel_name.strip()

    # If full url, parse path
    if channel_name.startswith("http://") or channel_name.startswith("https://"):
        p = urlparse(channel_name)
        path = p.path.strip("/")
        # possible formats: channel/UC..., @handle, user/legacyName
        parts = path.split("/")
        if len(parts) >= 1:
            first = parts[0]
            if first == "channel" and len(parts) > 1:
                return ("channelId", parts[1])
            if first == "user" and len(parts) > 1:
                return ("handle", parts[1])
            # handle '@handle' or '@something'
            if first.startswith("@"):
                return ("handle", first)
            # fallback: last segment
            return ("handle", parts[-1])

    # not a url
    if channel_name.startswith("UC") and len(channel_name) > 20:
        # likely a channelId
        return ("channelId", channel_name)
    if channel_name.startswith("@"):
        return ("handle", channel_name)
    # otherwise treat as handle/username
    return ("handle", channel_name)


def get_recent_video_captions_by_channel(channel_name: str, max_results: int = 30) -> List[Dict]:
    """
    Return list of dicts: {title, caption, video_id, video_url}
    Steps:
      1. Resolve channel id (via search if given a handle).
      2. Get uploads playlist id from channels().list(contentDetails).
      3. Fetch recent videos from that playlist.
      4. For each video, attempt to fetch transcript via youtube_transcript_api.
    """
    if not YOUTUBE_API_KEY or YOUTUBE_API_KEY == "1234":
        raise RuntimeError("YOUTUBE_API_KEY is not set or still the placeholder. Set environment variable YOUTUBE_API_KEY.")

    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

    mode, value = _extract_handle_from_input(channel_name)
    channel_id = None

    try:
        if mode == "channelId":
            channel_id = value
        else:
            # search for channel by handle/username
            handle = value
            # strip leading @ if present for search
            if handle.startswith("@"):
                handle = handle[1:]

            # Use search.list to find the channel ID
            search_resp = youtube.search().list(
                q=handle,
                type="channel",
                part="snippet",
                maxResults=1
            ).execute()

            items = search_resp.get("items", [])
            if not items:
                raise ValueError(f"Could not find a channel matching '{channel_name}'")

            channel_id = items[0]["snippet"]["channelId"]

        # Get uploads playlist
        ch_resp = youtube.channels().list(
            part="contentDetails",
            id=channel_id
        ).execute()
        ch_items = ch_resp.get("items", [])
        if not ch_items:
            raise ValueError(f"No channel details found for channel id {channel_id}")

        uploads_playlist_id = ch_items[0]["contentDetails"]["relatedPlaylists"]["uploads"]

        # Fetch videos from uploads playlist
        videos = []
        nextPageToken = None
        fetched = 0
        while fetched < max_results:
            resp = youtube.playlistItems().list(
                part="snippet",
                playlistId=uploads_playlist_id,
                maxResults=min(50, max_results - fetched),
                pageToken=nextPageToken
            ).execute()

            for item in resp.get("items", []):
                snippet = item.get("snippet", {})
                title = snippet.get("title")
                resource = snippet.get("resourceId", {})
                vid = resource.get("videoId")
                if vid:
                    videos.append({"video_id": vid, "title": title})
                    fetched += 1
                    if fetched >= max_results:
                        break

            nextPageToken = resp.get("nextPageToken")
            if not nextPageToken:
                break

        # For each video try to fetch transcript
        results = []
        for v in videos:
            vid = v["video_id"]
            title = v.get("title", "")
            caption_text = None
            try:
                # returns list of {'text':..., 'start':..., 'duration':...}
                transcript = YouTubeTranscriptApi.get_transcript(vid)
                # join texts
                caption_text = " ".join([t["text"].strip() for t in transcript if t.get("text")])
            except TranscriptsDisabled:
                logger.info(f"Transcripts disabled for video {vid}")
                caption_text = None
            except NoTranscriptFound:
                logger.info(f"No transcript for video {vid}")
                caption_text = None
            except CouldNotRetrieveTranscript:
                logger.info(f"Could not retrieve transcript for video {vid}")
                caption_text = None
            except Exception as e:
                # some other issue (video removed, etc.)
                logger.warning(f"Error fetching transcript for {vid}: {e}")
                caption_text = None

            results.append({
                "title": title,
                "video_id": vid,
                "video_url": f"https://www.youtube.com/watch?v={vid}",
                "caption": caption_text
            })

        return results

    finally:
        try:
            youtube.close()
        except Exception:
            pass


