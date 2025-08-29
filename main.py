import os
import re
from urllib.parse import urlparse, parse_qs

from apify_client import ApifyClient
from yt_dlp import YoutubeDL

def get_video_id(url: str) -> str | None:
    """Extracts the YouTube ID of a video from a URL."""
    parsed_url = urlparse(url)
    if parsed_url.hostname in ('youtu.be'):
        return parsed_url.path[1:]
    if parsed_url.hostname in ('www.youtube.com', 'youtube.com'):
        if parsed_url.path == '/watch':
            p = parse_qs(parsed_url.query)
            return p.get('v', [None])[0]
    return None

async def main() -> None:
    """
    The main function of the Apify actor.
    Downloads a video from YouTube and stores it in a key-value store.
    """
    async with ApifyClient() as client:
        actor_input = await client.actor_input() or {}
        video_url = actor_input.get('videoUrl')

        if not video_url:
            print("❌ Error: Video URL ('videoUrl') not provided. Solution.")
            return

        print(f"▶️ Start downloading the video: {video_url}")

        video_id = get_video_id(video_url)
        if not video_id:
            print("❌ Error: Unable to extract video ID from URL.")
            return

        safe_video_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
        output_filename = f"{safe_video_id}.mp4"
        output_path = f"/tmp/{output_filename}"

        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': output_path,
            'quiet': False,
        }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

            print(f"✅ Video has been successfully uploaded: {output_path}")

            if not os.path.exists(output_path):
                raise FileNotFoundError("The uploaded file was not found.")

            key_value_store = await client.key_value_store('default')
            with open(output_path, "rb") as f:
                await key_value_store.set_record(
                    key=output_filename,
                    value=f.read(),
                    content_type='video/mp4'
                )

            record_url = key_value_store.get_record_url(output_filename)
            print(f"📦 The video is saved in the Key-Value Store.")
            print(f"🔗 Download link: {record_url}")

            dataset = await client.dataset('default')
            await dataset.push_items([{"videoUrl": video_url, "downloadUrl": record_url}])

        except Exception as e:
            print(f"💥 Error: {e}")
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
                print(f"🧹 Temporary file deleted: {output_path}")
