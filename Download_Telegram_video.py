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

def get_downloaded_files():
    if os.path.exists(status_file):
        with open(status_file, 'r') as f:
            return set(f.read().splitlines())
    return set()

def save_downloaded_file(file_name):
    with open(status_file, 'a') as f:
        f.write(file_name + '\n')

async def download_media(message, downloaded_files, media_type, folder, semaphore):
    if media_type == 'video' and hasattr(message.media, 'video'):
        media_name = message.file.name or f"Video_{message.id}.mp4"
    elif media_type == 'image' and hasattr(message.media, 'photo'):
        media_name = message.file.name or f"Image_{message.id}.jpg"
    elif media_type == 'file' and hasattr(message.media, 'document'):
        media_name = message.file.name or f"File_{message.id}"
    else:
        return None  # Không phải loại media cần tải

    if media_name in downloaded_files:
        logging.info(f"{media_type.capitalize()} {media_name} already downloaded, skipping.")
        print(f"{media_type.capitalize()} {media_name} has already been downloaded. Skipping.")
        return None

    temp_file_path = os.path.join(folder, f"tmp_{media_name}")
    print(f"Starting download: {media_name}")

    def progress_callback(current, total):
        percent = (current / total) * 100
        print(f"\r{media_name}: {percent:.2f}%", end="", flush=True)

    try:
        async with semaphore:
            await client.download_media(
                message.media,
                file=temp_file_path,
                progress_callback=progress_callback
            )
        final_path = os.path.join(folder, media_name)
        shutil.move(temp_file_path, final_path)
        save_downloaded_file(media_name)
        print(f"\nDownload complete: {final_path}")
        logging.info(f"{media_type.capitalize()} downloaded successfully: {final_path}")
        return media_name
    except Exception as e:
        logging.error(f"Error downloading {media_type} {media_name}: {e}")
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        print(f"\nError downloading {media_name}.")
        return None

async def get_channel_info(channel_input):
    try:
        await client.start(phone=phone_number)
        if channel_input.startswith('https://t.me/'):
            channel = await client.get_entity(channel_input)
        else:
            channel = await client.get_entity(channel_input)

        videos = []
        images = []
        files = []

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

async def download_videos_or_images_or_files(channel_input, file_type):
    await client.start(phone=phone_number)
    logging.info(f"Successfully connected.")

    downloaded_files = get_downloaded_files()
    semaphore = asyncio.Semaphore(20)

    try:
        if file_type == "video":
            messages = [message async for message in client.iter_messages(channel_input) if message.media and hasattr(message.media, 'video')]
            print(f"Found {len(messages)} videos to download.")
            tasks = [download_media(message, downloaded_files, 'video', video_folder, semaphore) for message in messages]
        elif file_type == "image":
            messages = [message async for message in client.iter_messages(channel_input) if message.media and hasattr(message.media, 'photo')]
            print(f"Found {len(messages)} images to download.")
            tasks = [download_media(message, downloaded_files, 'image', image_folder, semaphore) for message in messages]
        elif file_type == "file":
            messages = [message async for message in client.iter_messages(channel_input) if message.media and hasattr(message.media, 'document')]
            print(f"Found {len(messages)} files to download.")
            tasks = [download_media(message, downloaded_files, 'file', file_folder, semaphore) for message in messages]
        else:
            print("Invalid file type selected.")
            return

        results = await asyncio.gather(*tasks)
        logging.info(f"\nDownloaded {len([r for r in results if r])} {file_type}s.")
    except Exception as e:
        logging.error(f"Error downloading {file_type}s: {e}")

async def main():
    while True:
        try:
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
                    try:
                        print("\nSelect file type to download:")
                        print("1. Download Video")
                        print("2. Download Image")
                        print("3. Download File")
                        print("4. Show media count")
                        print("5. Back to previous menu")
                        print("6. Exit")

                        file_choice = input("Enter your choice (1, 2, 3, 4, 5, or 6): ")

                        if file_choice == "6":
                            print("Exiting the program.")
                            return
                        elif file_choice == "5":
                            print("Returning to previous menu...\n")
                            break
                        elif file_choice == "4":
                            print("Fetching channel information...\n")
                            video_count, image_count, file_count, channel = await get_channel_info(channel_input)
                            if channel:
                                print(f"Channel Name: {channel.title} | Videos: {video_count} | Images: {image_count} | Files: {file_count}")
                            else:
                                print("Unable to fetch channel info.")
                        else:
                            if file_choice == "1":
                                file_type = "video"
                            elif file_choice == "2":
                                file_type = "image"
                            elif file_choice == "3":
                                file_type = "file"
                            else:
                                print("Invalid file type choice, please try again.")
                                continue

                            await download_videos_or_images_or_files(channel_input, file_type)
                    except Exception as e:
                        print(f"Error occurred in file type selection: {e}. Please try again.")
            elif choice == "3":
                print("Exiting the program.")
                break
            else:
                print("Invalid choice, please try again.")
        except Exception as e:
            print(f"Error occurred in method selection: {e}. Please try again.")

if __name__ == "__main__":
    asyncio.run(main())