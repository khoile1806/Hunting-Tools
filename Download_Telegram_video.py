import os
import shutil
import asyncio
import logging
from telethon import TelegramClient

logging.basicConfig(filename='download_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

api_id = ''
api_hash = ''
phone_number = ''

output_folder = 'videos'
os.makedirs(output_folder, exist_ok=True)
status_file = 'download_status.txt'
client = TelegramClient('session_name', api_id, api_hash)

def get_downloaded_videos():
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_downloaded_video(video_name):
    with open(status_file, 'a') as f:
        f.write(video_name + '\n')

async def download_video(message, downloaded_videos, semaphore):
    if message.media and hasattr(message.media, 'video'):
        video_name = message.file.name or f"Video_{message.id}.mp4"
        if video_name in downloaded_videos:
            logging.info(f"Video {video_name} already downloaded, skipping.")
            return None

        temp_file_path = os.path.join(output_folder, f"tmp_{video_name}")
        video_size = message.file.size / (1024 * 1024)

        print(f"Starting download: {video_name} - {video_size:.2f} MB")

        def progress_callback(current, total):
            percent = (current / total) * 100
            num_equals = int(percent // 2)
            progress_bar = f"====> {'=' * num_equals}{' ' * (50 - num_equals)} {percent:.2f}%"
            print(f"\r{video_name} - {video_size:.2f} MB: {progress_bar}", end="", flush=True)

        try:
            async with semaphore:
                await client.download_media(
                    message.media,
                    file=temp_file_path,
                    progress_callback=progress_callback
                )
            final_path = os.path.join(output_folder, video_name)
            shutil.move(temp_file_path, final_path)
            save_downloaded_video(video_name)
            print(f"\nDownload complete: {final_path}")
            logging.info(f"Video downloaded successfully: {final_path}")
            return video_name
        except Exception as e:
            logging.error(f"Error downloading video {video_name}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            print(f"\nError downloading {video_name}.")
            return None
    return None

async def download_videos(channel_input):
    await client.start(phone=phone_number)
    logging.info(f"Successfully connected.")

    downloaded_videos = get_downloaded_videos()
    semaphore = asyncio.Semaphore(20)

    try:
        if channel_input.startswith('https://t.me/'):
            channel = await client.get_entity(channel_input)
        else:
            channel = await client.get_entity(channel_input)

        messages = [message async for message in client.iter_messages(channel) if message.media and hasattr(message.media, 'video')]
        tasks = [download_video(message, downloaded_videos, semaphore) for message in messages]
        results = await asyncio.gather(*tasks)
        logging.info(f"\nDownloaded {len([r for r in results if r])} videos.")
    except Exception as e:
        logging.error(f"Error downloading videos: {e}")

while True:
    print("Select download method:")
    print("1. Download by channel name")
    print("2. Download by invite link")
    print("3. Exit")

    choice = input("Enter your choice (1, 2, or 3): ")

    if choice == "1":
        channel_name = input("Enter the channel name: ")
        with client:
            client.loop.run_until_complete(download_videos(channel_name))
        break
    elif choice == "2":
        channel_link = input("Enter the invite link: ")
        with client:
            client.loop.run_until_complete(download_videos(channel_link))
        break
    elif choice == "3":
        print("Exiting the program.")
        break
    else:
        print("Invalid choice, please try again.")