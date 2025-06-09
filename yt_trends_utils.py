# yt_trends_utils.py
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from datetime import datetime, timedelta
from pytrends.request import TrendReq

import os

YOUTUBE_API_KEY = "AIzaSyArcmO3SEp5xCHVOmgEBMDB6Zu4xTipICQ"  # or hardcode temporarily


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

