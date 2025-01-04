import os
import shutil
import asyncio
import logging
from telethon import TelegramClient, types
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn
from rich.table import Table
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.panel import Panel
from rich.text import Text

logging.basicConfig(filename='download_log.txt', level=logging.INFO, format='%(asctime)s - %(message)s')
console = Console()

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

async def download_media(message, downloaded_files, semaphore, media_type, progress, task_id, retries=3):
    if media_type == "video" and isinstance(message.media, types.MessageMediaDocument):
        file_name = message.file.name or f"Video_{message.id}.mp4"
        file_folder_path = video_folder
        duration = get_video_duration(message.media.document.attributes) if message.media.document else "Unknown duration"
    elif media_type == "photo" and isinstance(message.media, types.MessageMediaPhoto):
        file_name = message.file.name or f"Image_{message.id}.jpg"
        file_folder_path = image_folder
        duration = None
    elif media_type == "document" and isinstance(message.media, types.MessageMediaDocument):
        file_name = message.file.name or f"File_{message.id}"
        file_folder_path = file_folder
        duration = None
    else:
        return None

    if file_name in downloaded_files:
        console.print(f"[yellow]{media_type.capitalize()} {file_name} already downloaded, skipping.[/yellow]")
        return None

    file_size = format_size(message.file.size) if message.file else "Unknown size"
    temp_file_path = os.path.join(file_folder_path, f"tmp_{file_name}")
    console.print(f"[green]Starting download: {file_name} | Size: {file_size} | {'Duration: ' + duration if duration else ''}[/green]")

    def progress_callback(current, total):
        progress.update(task_id, completed=current)

    for attempt in range(retries):
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
            console.print(f"[green]Download complete: {final_path}[/green]")
            logging.info(f"{media_type.capitalize()} downloaded successfully: {final_path}")
            return file_name
        except Exception as e:
            logging.error(f"Attempt {attempt + 1} failed: Error downloading {media_type} {file_name}: {e}")
            console.print(f"[red]Attempt {attempt + 1} failed: Error downloading {file_name}.[/red]")
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            if attempt == retries - 1:
                console.print(f"[red]Failed to download {file_name} after {retries} attempts.[/red]")
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
                if isinstance(message.media, types.MessageMediaDocument):
                    if any(isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes):
                        videos.append(message)
                    else:
                        files.append(message)
                elif isinstance(message.media, types.MessageMediaPhoto):
                    images.append(message)

        if isinstance(channel, types.Channel):
            channel_name = channel.title
        else:
            channel_name = channel.first_name or channel.username or "Unknown"

        return len(videos), len(images), len(files), channel_name
    except Exception as e:
        logging.error(f"Error getting channel info: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return 0, 0, 0, None

async def download_by_type(channel_input, media_type):
    await client.start(phone=phone_number)
    downloaded_files = get_downloaded_files()
    semaphore = asyncio.Semaphore(10)
    try:
        messages = [
            message async for message in client.iter_messages(channel_input)
            if message.media and (
                (media_type == "photo" and isinstance(message.media, types.MessageMediaPhoto)) or
                (media_type == "video" and isinstance(message.media, types.MessageMediaDocument) and
                 any(isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes)) or
                (media_type == "document" and isinstance(message.media, types.MessageMediaDocument) and
                 not any(isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes))
            )
        ]

        total_files = len(messages)
        if total_files == 0:
            console.print(f"[yellow]No {media_type}s found to download.[/yellow]")
            return

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            overall_task = progress.add_task(f"[green]Downloading {total_files} {media_type}s...", total=total_files)

            file_tasks = {}
            for message in messages:
                file_name = message.file.name or f"{media_type}_{message.id}"
                file_tasks[message.id] = progress.add_task(f"[cyan]{file_name}", total=message.file.size)

            for message in messages:
                file_name = await download_media(message, downloaded_files, semaphore, media_type, progress, file_tasks[message.id])
                if file_name:
                    progress.update(overall_task, advance=1)

            console.print(f"[green]Downloaded {len([r for r in file_tasks.values() if r])} {media_type}s out of {total_files}.[/green]")
    except Exception as e:
        logging.error(f"Error downloading {media_type}s: {e}")
        console.print(f"[red]Error downloading {media_type}s: {e}[/red]")

def display_main_menu():
    console.clear()
    console.print(Panel.fit(
        Text("Telegram Media Downloader", style="bold blue"),
        subtitle="by Your Name",
        border_style="green"
    ))

    menu_options = [
        ("1", "Download by channel name"),
        ("2", "Download by invite link"),
        ("3", "Exit")
    ]

    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    for option, description in menu_options:
        menu_table.add_row(
            Text(option, style="bold yellow"),
            Text(description, style="cyan")
        )

    console.print(Panel(menu_table, title="Main Menu", border_style="blue"))

def display_file_type_menu(channel_name):
    console.clear()
    console.print(Panel.fit(
        Text(f"Downloading from: {channel_name}", style="bold blue"),
        border_style="green"
    ))

    menu_options = [
        ("1", "Download Video"),
        ("2", "Download Image"),
        ("3", "Download File"),
        ("4", "Show media count"),
        ("5", "Back to Main Menu"),
        ("6", "Exit")
    ]

    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    for option, description in menu_options:
        menu_table.add_row(
            Text(option, style="bold yellow"),
            Text(description, style="cyan")
        )

    console.print(Panel(menu_table, title="File Type Menu", border_style="blue"))

async def main():
    while True:
        display_main_menu()
        choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3"])

        if choice in [1, 2]:
            if choice == 1:
                channel_input = Prompt.ask("Enter the channel name")
            else:
                channel_input = Prompt.ask("Enter the invite link")

            while True:
                display_file_type_menu(channel_input)
                file_choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])

                if file_choice == 6:
                    console.print("[bold]Exiting the program.[/bold]")
                    return
                elif file_choice == 5:
                    break
                elif file_choice == 4:
                    console.print("[bold]Fetching channel information...[/bold]")
                    video_count, image_count, file_count, channel_name = await get_channel_info(channel_input)
                    if channel_name:
                        table = Table(title="Channel Information")
                        table.add_column("Channel Name", justify="center")
                        table.add_column("Videos", justify="center")
                        table.add_column("Images", justify="center")
                        table.add_column("Files", justify="center")
                        table.add_row(channel_name, str(video_count), str(image_count), str(file_count))
                        console.print(table)
                    else:
                        console.print("[red]Unable to fetch channel info.[/red]")
                else:
                    media_type = {1: "video", 2: "photo", 3: "document"}.get(file_choice)
                    if not media_type:
                        console.print("[red]Invalid choice, please try again.[/red]")
                        continue
                    await download_by_type(channel_input, media_type)
        elif choice == 3:
            console.print("[bold]Exiting the program.[/bold]")
            break
        else:
            console.print("[red]Invalid choice, please try again.[/red]")

if __name__ == "__main__":
    asyncio.run(main())