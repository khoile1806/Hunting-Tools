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

async def download_video(message, downloaded_files, semaphore):
    if message.media and hasattr(message.media, 'video'):
        video_name = message.file.name or f"Video_{message.id}.mp4"
        if video_name in downloaded_files:
            logging.info(f"Video {video_name} already downloaded, skipping.")
            return None

        temp_file_path = os.path.join(video_folder, f"tmp_{video_name}")
        print(f"Starting download: {video_name}")

        def progress_callback(current, total):
            percent = (current / total) * 100
            print(f"\r{video_name}: {percent:.2f}%", end="", flush=True)

        try:
            async with semaphore:
                await client.download_media(
                    message.media,
                    file=temp_file_path,
                    progress_callback=progress_callback
                )
            final_path = os.path.join(video_folder, video_name)
            shutil.move(temp_file_path, final_path)
            save_downloaded_file(video_name)
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

async def download_image(message, downloaded_files, semaphore):
    if message.media and hasattr(message.media, 'photo'):
        image_name = message.file.name or f"Image_{message.id}.jpg"
        if image_name in downloaded_files:
            logging.info(f"Image {image_name} already downloaded, skipping.")
            return None

        temp_file_path = os.path.join(image_folder, f"tmp_{image_name}")
        print(f"Starting download: {image_name}")

        def progress_callback(current, total):
            percent = (current / total) * 100
            print(f"\r{image_name}: {percent:.2f}%", end="", flush=True)

        try:
            async with semaphore:
                await client.download_media(
                    message.media,
                    file=temp_file_path,
                    progress_callback=progress_callback
                )
            final_path = os.path.join(image_folder, image_name)
            shutil.move(temp_file_path, final_path)
            save_downloaded_file(image_name)
            print(f"\nDownload complete: {final_path}")
            logging.info(f"Image downloaded successfully: {final_path}")
            return image_name
        except Exception as e:
            logging.error(f"Error downloading image {image_name}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            print(f"\nError downloading {image_name}.")
            return None
    return None

async def download_file(message, downloaded_files, semaphore):
    if message.media and hasattr(message.media, 'document'):
        file_name = message.file.name or f"File_{message.id}"
        if file_name in downloaded_files:
            logging.info(f"File {file_name} already downloaded, skipping.")
            return None

        temp_file_path = os.path.join(file_folder, f"tmp_{file_name}")
        print(f"Starting download: {file_name}")

        def progress_callback(current, total):
            percent = (current / total) * 100
            print(f"\r{file_name}: {percent:.2f}%", end="", flush=True)

        try:
            async with semaphore:
                await client.download_media(
                    message.media,
                    file=temp_file_path,
                    progress_callback=progress_callback
                )
            final_path = os.path.join(file_folder, file_name)
            shutil.move(temp_file_path, final_path)
            save_downloaded_file(file_name)
            print(f"\nDownload complete: {final_path}")
            logging.info(f"File downloaded successfully: {final_path}")
            return file_name
        except Exception as e:
            logging.error(f"Error downloading file {file_name}: {e}")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            print(f"\nError downloading {file_name}.")
            return None
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

    video_count, image_count, file_count, channel = await get_channel_info(channel_input)
    if channel:
        print(f"Channel Name: {channel.title} | Number of Videos: {video_count} | Number of Images: {image_count} | Number of Files: {file_count}")
    else:
        print("Unable to fetch channel info.")
        return

    downloaded_files = get_downloaded_files()
    semaphore = asyncio.Semaphore(20)

    try:
        if file_type == "video":
            messages = [message async for message in client.iter_messages(channel) if message.media and hasattr(message.media, 'video')]
            tasks = [download_video(message, downloaded_files, semaphore) for message in messages]
        elif file_type == "image":
            messages = [message async for message in client.iter_messages(channel) if message.media and hasattr(message.media, 'photo')]
            tasks = [download_image(message, downloaded_files, semaphore) for message in messages]
        elif file_type == "file":
            messages = [message async for message in client.iter_messages(channel) if message.media and hasattr(message.media, 'document')]
            tasks = [download_file(message, downloaded_files, semaphore) for message in messages]
        else:
            print("Invalid file type selected.")
            return

        results = await asyncio.gather(*tasks)
        logging.info(f"\nDownloaded {len([r for r in results if r])} {file_type}s.")
    except Exception as e:
        logging.error(f"Error downloading {file_type}s: {e}")

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

            print("\nFetching channel information...\n")
            video_count, image_count, file_count, channel = await get_channel_info(channel_input)
            if channel:
                print(f"Channel Name: {channel.title} | Videos: {video_count} | Images: {image_count} | Files: {file_count}")
            else:
                print("Unable to fetch channel info.")
                continue

            print("\nSelect file type to download:")
            print("1. Video")
            print("2. Image")
            print("3. File")
            print("4. Exit")

            file_choice = input("Enter your choice (1, 2, 3, or 4): ")

            if file_choice == "4":
                print("Exiting the program.")
                break  # Thoát chương trình
            elif file_choice == "1":
                file_type = "video"
            elif file_choice == "2":
                file_type = "image"
            elif file_choice == "3":
                file_type = "file"
            else:
                print("Invalid file type choice, please try again.")
                continue

            await download_videos_or_images_or_files(channel_input, file_type)
            break
        elif choice == "3":
            print("Exiting the program.")
            break
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    asyncio.run(main())

