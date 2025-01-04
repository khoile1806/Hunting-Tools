import os
import shutil
import asyncio
import logging
from telethon import TelegramClient

logging.basicConfig(filename='download_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')

api_id = ''
api_hash = ''
phone_number = ''

output_folder = 'downloads'
video_folder = os.path.join(output_folder, 'videos')
image_folder = os.path.join(output_folder, 'images')
file_folder = os.path.join(output_folder, 'files')
os.makedirs(video_folder, exist_ok=True)
os.makedirs(image_folder, exist_ok=True)
os.makedirs(file_folder, exist_ok=True)

status_file = 'download_status.txt'
client = TelegramClient('session_name', api_id, api_hash)

def format_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 ** 2:
        return f"{size_in_bytes / 1024:.2f} KB"
    elif size_in_bytes < 1024 ** 3:
        return f"{size_in_bytes / (1024 ** 2):.2f} MB"
    else:
        return f"{size_in_bytes / (1024 ** 3):.2f} GB"

def get_video_duration(attributes):
    for attr in attributes:
        if hasattr(attr, "duration"):
            minutes, seconds = divmod(attr.duration, 60)
            return f"{minutes}m {seconds}s"
    return "Unknown duration"

def get_downloaded_files():
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_downloaded_file(file_name):
    with open(status_file, 'a') as f:
        f.write(file_name + '\n')

async def download_media(message, downloaded_files, semaphore, media_type):
    if media_type == "video" and hasattr(message.media, 'video'):
        file_name = message.file.name or f"Video_{message.id}.mp4"
        file_folder_path = video_folder
        duration = get_video_duration(message.media.document.attributes) if message.media.document else "Unknown duration"
    elif media_type == "image" and hasattr(message.media, 'photo'):
        file_name = message.file.name or f"Image_{message.id}.jpg"
        file_folder_path = image_folder
        duration = None
    elif media_type == "file" and hasattr(message.media, 'document'):
        file_name = message.file.name or f"File_{message.id}"
        file_folder_path = file_folder
        duration = None
    else:
        return None

    if file_name in downloaded_files:
        logging.info(f"{media_type.capitalize()} {file_name} already downloaded, skipping.")
        print(f"{media_type.capitalize()} {file_name} already downloaded, skipping.")
        return None

    file_size = format_size(message.file.size) if message.file else "Unknown size"
    temp_file_path = os.path.join(file_folder_path, f"tmp_{file_name}")
    print(f"Starting download: {file_name} | Size: {file_size} | {'Duration: ' + duration if duration else ''}")

    def progress_callback(current, total):
        percent = (current / total) * 100
        print(f"\r{file_name}: {percent:.2f}% ({format_size(current)} / {file_size})", end="", flush=True)

    try:
        async with semaphore:
            await client.download_media(
                message.media,
                file=temp_file_path,
                progress_callback=progress_callback
            )
        final_path = os.path.join(file_folder_path, file_name)
        shutil.move(temp_file_path, final_path)
        save_downloaded_file(file_name)
        print(f"\nDownload complete: {final_path}")
        logging.info(f"{media_type.capitalize()} downloaded successfully: {final_path}")
        return file_name
    except Exception as e:
        logging.error(f"Error downloading {media_type} {file_name}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"\nError downloading {file_name}.")
        return None

async def get_channel_info(channel_input):
    try:
        await client.start(phone=phone_number)
        if channel_input.startswith('https://t.me/'):
            channel = await client.get_entity(channel_input)
        else:
            channel = await client.get_entity(channel_input)

        videos, images, files = [], [], []

        async for message in client.iter_messages(channel):
            if message.media:
                if hasattr(message.media, 'video'):
                    videos.append(message)
                elif hasattr(message.media, 'photo'):
                    images.append(message)
                elif hasattr(message.media, 'document'):
                    files.append(message)

        return len(videos), len(images), len(files), channel
    except Exception as e:
        logging.error(f"Error getting channel info: {e}")
        print(f"Error: {e}")
        return 0, 0, 0, None

async def download_by_type(channel_input, media_type):
    await client.start(phone=phone_number)
    downloaded_files = get_downloaded_files()
    semaphore = asyncio.Semaphore(10)

    try:
        messages = [
            message async for message in client.iter_messages(channel_input)
            if message.media and hasattr(message.media, media_type)
        ]
        tasks = [download_media(message, downloaded_files, semaphore, media_type) for message in messages]
        results = await asyncio.gather(*tasks)
        logging.info(f"\nDownloaded {len([r for r in results if r])} {media_type}s.")
    except Exception as e:
        logging.error(f"Error downloading {media_type}s: {e}")
        print(f"Error downloading {media_type}s: {e}")

async def main():
    while True:
        print("Select download method:")
        print("1. Download by channel name")
        print("2. Download by invite link")
        print("3. Exit")

        choice = input("Enter your choice (1, 2, or 3): ")

        if choice in ["1", "2"]:
            if choice == "1":
                channel_input = input("Enter the channel name: ")
            else:
                channel_input = input("Enter the invite link: ")

            while True:
                print("\nSelect file type to download:")
                print("1. Download Video")
                print("2. Download Image")
                print("3. Download File")
                print("4. Show media count")
                print("5. Back")
                print("6. Exit")

                file_choice = input("Enter your choice (1, 2, 3, 4, 5, or 6): ")

                if file_choice == "6":
                    print("Exiting the program.")
                    return
                elif file_choice == "5":
                    break
                elif file_choice == "4":
                    print("Fetching channel information...\n")
                    video_count, image_count, file_count, channel = await get_channel_info(channel_input)
                    if channel:
                        print(f"Channel Name: {channel.title} | Videos: {video_count} | Images: {image_count} | Files: {file_count}")
                    else:
                        print("Unable to fetch channel info.")
                else:
                    media_type = {"1": "video", "2": "photo", "3": "document"}.get(file_choice)
                    if not media_type:
                        print("Invalid choice, please try again.")
                        continue
                    await download_by_type(channel_input, media_type)
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    asyncio.run(main())