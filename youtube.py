import asyncio
import logging
import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, FSInputFile
from yt_dlp import YoutubeDL

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
DOWNLOADS_DIR = "downloads"

dp = Dispatcher()

# Create the downloads directory if it doesn't exist
if not os.path.exists(DOWNLOADS_DIR):
    os.makedirs(DOWNLOADS_DIR)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        f"Hello, {html.bold(message.from_user.full_name)}! Send me a YouTube URL, and I'll fetch the video or short "
        f"for you!")


@dp.message()
async def echo_handler(message: Message) -> None:
    url = message.text
    await message.answer("Downloading...")
    if "youtube.com" in url or "youtu.be" in url:
        await download_youtube_video(message, url)
    else:
        await message.answer(f"Unknown command or invalid URL: {html.bold(url)}")


async def download_youtube_video(message: Message, url: str):
    # Configure yt-dlp
    ydl_opts = {
        'format': 'best',  # Download the best available quality
        'outtmpl': f'{DOWNLOADS_DIR}/%(title)s.%(ext)s',  # Save to 'downloads' folder
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)  # Download the video
            video_title = info['title']
            video_ext = info['ext']
            video_file_path = f"{DOWNLOADS_DIR}/{video_title}.{video_ext}"  # Construct the file path

            # Notify user that the download is complete

            await message.answer(f"Video downloaded: {html.bold(video_title)}. Sending the file...")

            # Send the video file to the user
            video_file = FSInputFile(video_file_path)  # Use FSInputFile for the file path
            await message.answer_video(video=video_file)

            # Save the current timestamp when the video was downloaded
            with open(f"{video_file_path}.timestamp", "w") as timestamp_file:
                timestamp_file.write(str(datetime.now()))

    except Exception as e:
        await message.answer(f"Failed to download video. Error: {str(e)}")


async def delete_old_files():
    """Function to delete files older than 2 days from the downloads directory."""
    while True:
        now = datetime.now()
        two_days_ago = now - timedelta(days=1)

        for filename in os.listdir(DOWNLOADS_DIR):
            # Check if there's a timestamp file for the downloaded video
            if filename.endswith(".timestamp"):
                file_path = os.path.join(DOWNLOADS_DIR, filename)

                # Read the timestamp from the file
                with open(file_path, "r") as timestamp_file:
                    file_timestamp = datetime.fromisoformat(timestamp_file.read().strip())

                # If the file is older than 2 days, delete it and its associated video
                if file_timestamp < two_days_ago:
                    video_file = file_path.replace(".timestamp", "")
                    try:
                        os.remove(video_file)  # Delete the video file
                        os.remove(file_path)  # Delete the timestamp file
                        logging.info(f"Deleted old video file: {video_file}")
                    except OSError as e:
                        logging.error(f"Error deleting file {video_file}: {e}")

        # Sleep for 24 hours before the next cleanup
        await asyncio.sleep(86400)  # 86400 seconds = 24 hours


async def main() -> None:
    bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    # Start the deletion task to run in the background
    asyncio.create_task(delete_old_files())

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

"""git init
git add .
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/ixlos23/you_tube_saver.git
git push -u origin main"""