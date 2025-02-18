import os
import shutil
import json
import asyncio
import logging
from rich.text import Text
from textwrap import shorten
from rich.panel import Panel
from rich.table import Table
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from telethon import TelegramClient, types
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, TaskProgressColumn

# https://my.telegram.org/auth

main_folder = 'telegram_downloads'
os.makedirs(main_folder, exist_ok=True)

output_folder = os.path.join(main_folder, 'downloads')
video_folder = os.path.join(output_folder, 'videos')
image_folder = os.path.join(output_folder, 'images')
file_folder = os.path.join(output_folder, 'files')
status_file = os.path.join(main_folder, 'download_status.txt')
log_file = os.path.join(main_folder, 'download_log.txt')
session_file = os.path.join(main_folder, 'session_name.session')
config_file = os.path.join(main_folder, 'config.json')
accounts_file = os.path.join(main_folder, 'accounts.json')

os.makedirs(video_folder, exist_ok=True)
os.makedirs(image_folder, exist_ok=True)
os.makedirs(file_folder, exist_ok=True)

logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(message)s')
console = Console()

accounts = []
current_account_index = 0

def add_account(api_id, api_hash, phone_number):
    session_file = os.path.join(main_folder, f"session_{phone_number}.session")
    accounts.append({
        "api_id": api_id,
        "api_hash": api_hash,
        "phone_number": phone_number,
        "session_file": session_file
    })
    save_accounts()
    console.print("[green]Account added successfully.[/green]")

def save_accounts():
    with open(accounts_file, 'w') as file:
        json.dump(accounts, file, indent=4)

def load_accounts():
    if os.path.exists(accounts_file):
        with open(accounts_file, 'r') as file:
            return json.load(file)
    return []

def delete_account(account_index):
    if 0 <= account_index < len(accounts):
        deleted_account = accounts.pop(account_index)
        if os.path.exists(deleted_account["session_file"]):
            os.remove(deleted_account["session_file"])
        save_accounts()
        console.print("[green]Account deleted successfully.[/green]")
    else:
        console.print("[red]Invalid account index.[/red]")

async def switch_account():
    global current_account_index, client

    if len(accounts) < 2:
        console.print("[red]Not enough accounts to switch.[/red]")
        return

    if client.is_connected():
        await client.disconnect()

    current_account_index = (current_account_index + 1) % len(accounts)
    account = accounts[current_account_index]

    console.print(f"[yellow]Switching to account: {account['phone_number']}...[/yellow]")
    session_path = os.path.join(main_folder, f"session_{account['phone_number']}.session")
    if os.path.exists(session_path):
        os.remove(session_path)
        console.print(f"[red]Deleted old session file for {account['phone_number']}.[/red]")

    client = TelegramClient(session_path, account["api_id"], account["api_hash"])

    if not client.is_connected():
        await client.connect()
        if not await client.is_user_authorized():
            await client.start(account["phone_number"])

    console.print(f"[green]Successfully switched to account: {account['phone_number']}[/green]")

async def manage_accounts():
    global accounts
    accounts = load_accounts()
    while True:
        console.print(Panel.fit(
            Text("Account Management Menu", style="bold blue"),
            border_style="green"
        ))
        console.print("[1] Add new account")
        console.print("[2] Switch account")
        console.print("[3] List all accounts")
        console.print("[4] Delete account")
        console.print("[5] Back to main menu")
        choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"])

        if choice == 1:
            api_id = Prompt.ask("Enter your API ID")
            api_hash = Prompt.ask("Enter your API Hash")
            phone_number = Prompt.ask("Enter your Phone Number")
            add_account(api_id, api_hash, phone_number)
        elif choice == 2:
            if len(accounts) > 1:
                await switch_account()
            else:
                console.print("[red]Not enough accounts to switch.[/red]")
        elif choice == 3:
            if accounts:
                table = Table(title="Accounts List")
                table.add_column("Index", justify="center")
                table.add_column("Phone Number", justify="center")
                table.add_column("API ID", justify="center")
                table.add_column("API Hash", justify="center")
                for idx, account in enumerate(accounts):
                    table.add_row(
                        str(idx + 1),
                        account["phone_number"],
                        account["api_id"],
                        account["api_hash"]
                    )
                console.print(table)
            else:
                console.print("[red]No accounts found.[/red]")
        elif choice == 4:
            if accounts:
                account_index = IntPrompt.ask("Enter the account index to delete", choices=[str(i + 1) for i in range(len(accounts))]) - 1
                delete_account(account_index)
            else:
                console.print("[red]No accounts to delete.[/red]")
        elif choice == 5:
            break
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")

def load_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as file:
            content = file.read().strip()
            if content:
                return json.loads(content)
    return {}

def save_config(api_id, api_hash, phone_number):
    with open(config_file, 'w') as file:
        json.dump({"api_id": api_id, "api_hash": api_hash, "phone_number": phone_number}, file)

def get_api_config():
    config = load_config()
    if not config.get("api_id") or not config.get("api_hash") or not config.get("phone_number"):

        console.print("[bold blue]Please provide your Telegram API credentials.[/bold blue]")
        console.print("[yellow]You can obtain these credentials from the Telegram website:[/yellow] [underline]https://my.telegram.org/auth[/underline]")
        console.print("[yellow]Steps to follow:[/yellow]")
        console.print("  1. Log in with your Telegram account.")
        console.print("  2. Go to the 'API Development Tools' section.")
        console.print("  3. Create a new app to get your API ID and API Hash.")
        console.print("  4. Use the phone number associated with your Telegram account.")

        api_id = Prompt.ask("Enter your API ID")
        api_hash = Prompt.ask("Enter your API Hash")
        phone_number = Prompt.ask("Enter your Phone Number")
        save_config(api_id, api_hash, phone_number)
        return api_id, api_hash, phone_number
    return config["api_id"], config["api_hash"], config["phone_number"]

api_id, api_hash, phone_number = get_api_config()
client = TelegramClient(session_file, api_id, api_hash)

def manage_api_config():
    while True:
        console.print(Panel.fit(
            Text("API Management Menu", style="bold blue"),
            border_style="green"
        ))
        console.print("[1] Show API credentials")
        console.print("[2] Delete API credentials")
        console.print("[3] Update API credentials")
        console.print("[4] Back to main menu")
        choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4"])

        if choice == 1:
            show_api_credentials()
        elif choice == 2:
            delete_api_credentials()
        elif choice == 3:
            update_api_credentials()
        elif choice == 4:
            break
        else:
            console.print("[red]Invalid choice. Please try again.[/red]")

def show_api_credentials():
    config = load_config()
    if config:
        console.print("[bold yellow]Current API Credentials:[/bold yellow]")
        console.print(f"API ID: {config.get('api_id', 'Not set')}")
        console.print(f"API Hash: {config.get('api_hash', 'Not set')}")
        console.print(f"Phone Number: {config.get('phone_number', 'Not set')}")
    else:
        console.print("[red]No API credentials found.[/red]")

def delete_api_credentials():
    if os.path.exists(config_file):
        os.remove(config_file)
        console.print("[green]API credentials deleted successfully.[/green]")
    else:
        console.print("[red]No API credentials to delete.[/red]")

def update_api_credentials():
    console.print("[bold blue]Please provide your Telegram API credentials.[/bold blue]")
    console.print(
        "[yellow]You can obtain these credentials from the Telegram website:[/yellow] [underline]https://my.telegram.org/auth[/underline]")
    console.print("[yellow]Steps to follow:[/yellow]")
    console.print("  1. Log in with your Telegram account.")
    console.print("  2. Go to the 'API Development Tools' section.")
    console.print("  3. Create a new app to get your API ID and API Hash.")
    console.print("  4. Use the phone number associated with your Telegram account.")
    api_id = Prompt.ask("Enter your new API ID")
    api_hash = Prompt.ask("Enter your new API Hash")
    phone_number = Prompt.ask("Enter your new Phone Number")
    save_config(api_id, api_hash, phone_number)
    console.print("[green]API credentials updated successfully.[/green]")

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

    file_name = get_unique_filename(file_folder_path, file_name)
    file_size = message.file.size if message.file else 0
    file_size_str = format_size(file_size)
    temp_file_path = os.path.join(file_folder_path, f"tmp_{file_name}")
    console.print(f"[green]Starting download: {file_name} | Size: {file_size_str} | {'Duration: ' + duration if duration else ''}[/green]")

    def progress_callback(current, total):
        progress.update(task_id, completed=current, description=f"[cyan]Downloading {file_name} ({format_size(current)}/{file_size_str})...[/cyan]")

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

def get_unique_filename(file_folder_path, file_name):
    base_name, extension = os.path.splitext(file_name)
    counter = 1
    while os.path.exists(os.path.join(file_folder_path, file_name)):
        file_name = f"{base_name}_{counter}{extension}"
        counter += 1
    return file_name


async def download_by_type(channel_input, media_type, start_date=None, end_date=None):
    if not client.is_connected():
        await client.connect()
        if not await client.is_user_authorized():
            await client.start(phone=phone_number)

    downloaded_files = get_downloaded_files()
    semaphore = asyncio.Semaphore(20)
    success_count = 0
    try:
        messages = [
            message async for message in client.iter_messages(channel_input)
            if message.media and (
                    (media_type == "photo" and isinstance(message.media, types.MessageMediaPhoto)) or
                    (media_type == "video" and isinstance(message.media, types.MessageMediaDocument) and
                     any(isinstance(attr, types.DocumentAttributeVideo) for attr in
                         message.media.document.attributes)) or
                    (media_type == "document" and isinstance(message.media, types.MessageMediaDocument) and
                     not any(
                         isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes))
            )
        ]
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, "%d/%m/%Y")
            end_date_obj = datetime.strptime(end_date, "%d/%m/%Y")
            messages = [
                message for message in messages
                if start_date_obj <= message.date.replace(tzinfo=None) <= end_date_obj
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
                file_name = await download_media(message, downloaded_files, semaphore, media_type, progress,
                                                 file_tasks[message.id])
                if file_name:
                    success_count += 1
                    progress.update(overall_task, advance=1)

        console.print(f"[green]Downloaded {success_count} {media_type}s out of {total_files}.[/green]")

    except Exception as e:
        logging.error(f"Error downloading {media_type}s: {e}")
        console.print(f"[red]Error downloading {media_type}s: {e}[/red]")

    finally:
        if client.is_connected():
            await client.disconnect()

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
        ("3", "Download by Chat ID"),
        ("4", "List all chats/channels/groups"),
        ("5", "Manage API Configuration"),
        ("6", "Manage Accounts"),
        ("7", "Exit")
    ]
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    for option, description in menu_options:
        menu_table.add_row(
            Text(option, style="bold yellow"),
            Text(description, style="cyan")
        )

    console.print(Panel(menu_table, title="Main Menu", border_style="blue"))

async def get_channel_info(channel_input):
    try:
        if not client.is_connected():
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=phone_number)

        channel = await client.get_entity(channel_input)
        video_count = 0
        image_count = 0
        file_count = 0
        async for message in client.iter_messages(channel):
            if message.media:
                if isinstance(message.media, types.MessageMediaPhoto):
                    image_count += 1
                elif isinstance(message.media, types.MessageMediaDocument):
                    attributes = message.media.document.attributes
                    if any(isinstance(attr, types.DocumentAttributeVideo) for attr in attributes):
                        video_count += 1
                    else:
                        file_count += 1

        channel_name = channel.title if hasattr(channel, "title") else "Unknown"
        return video_count, image_count, file_count, channel_name
    except Exception as e:
        logging.error(f"Error fetching channel info: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return 0, 0, 0, None

async def get_timeline_overview(channel_input, start_date=None, end_date=None):
    try:
        if not client.is_connected():
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=phone_number)

        channel = await client.get_entity(channel_input)
        timeline = {}
        async for message in client.iter_messages(channel):
            message_date = message.date.strftime("%d/%m/%Y")
            if (not start_date and not end_date) or (start_date and end_date and start_date <= message_date <= end_date) or (start_date and not end_date and message_date == start_date):
                if message.media:
                    if message_date not in timeline:
                        timeline[message_date] = {"videos": 0, "images": 0, "files": 0}
                    if isinstance(message.media, types.MessageMediaPhoto):
                        timeline[message_date]["images"] += 1
                    elif isinstance(message.media, types.MessageMediaDocument):
                        attributes = message.media.document.attributes
                        if any(isinstance(attr, types.DocumentAttributeVideo) for attr in attributes):
                            timeline[message_date]["videos"] += 1
                        else:
                            timeline[message_date]["files"] += 1

        return timeline, channel.title if hasattr(channel, "title") else "Unknown"
    except Exception as e:
        logging.error(f"Error fetching timeline overview: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return {}, None

async def get_detailed_timeline(channel_input, start_date=None, end_date=None):
    try:
        if not client.is_connected():
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=phone_number)

        channel = await client.get_entity(channel_input)
        detailed_timeline = []
        async for message in client.iter_messages(channel):
            message_date = message.date.strftime("%d/%m/%Y")

            if (not start_date and not end_date) or (start_date and end_date and start_date <= message_date <= end_date) or (start_date and not end_date and message_date == start_date):
                if message.media:
                    file_info = {
                        "type": "File",
                        "name": None,
                        "size": None,
                        "extension": None,
                        "resolution": None,
                        "duration": None
                    }
                    if hasattr(message.file, "name") and message.file.name:
                        file_info["name"] = message.file.name
                        file_info["extension"] = os.path.splitext(message.file.name)[1].lower()
                    else:
                        file_info["name"] = f"File_{message.id}"
                        file_info["extension"] = "Unknown"

                    if hasattr(message.file, "size"):
                        file_info["size"] = format_size(message.file.size)
                    else:
                        file_info["size"] = "Unknown size"

                    if isinstance(message.media, types.MessageMediaPhoto):
                        file_info["type"] = "Image"
                        if hasattr(message.media, "photo") and hasattr(message.media.photo, "sizes"):
                            for size in message.media.photo.sizes:
                                if hasattr(size, "w") and hasattr(size, "h"):
                                    file_info["resolution"] = f"{size.w}x{size.h}"
                                    break

                    elif isinstance(message.media, types.MessageMediaDocument):
                        attributes = message.media.document.attributes
                        if any(isinstance(attr, types.DocumentAttributeVideo) for attr in attributes):
                            file_info["type"] = "Video"
                            file_info["duration"] = get_video_duration(attributes)
                            for attr in attributes:
                                if isinstance(attr, types.DocumentAttributeVideo):
                                    file_info["resolution"] = f"{attr.w}x{attr.h}"
                                    break

                    detailed_timeline.append(file_info)

        return detailed_timeline
    except Exception as e:
        logging.error(f"Error fetching detailed timeline: {e}")
        console.print(f"[red]Error: {e}[/red]")
        return None

async def download_by_name(channel_input, file_name):
    try:
        if not client.is_connected():
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=phone_number)

        downloaded_files = get_downloaded_files()
        semaphore = asyncio.Semaphore(10)
        matching_messages = []
        async for message in client.iter_messages(channel_input):
            if message.media:
                current_file_name = message.file.name or f"File_{message.id}"
                if file_name.lower() in current_file_name.lower():
                    matching_messages.append(message)

        if not matching_messages:
            console.print(f"[yellow]No files found containing '{file_name}'.[/yellow]")
            return

        table = Table(title=f"Files containing '{file_name}'")
        table.add_column("#", justify="center")
        table.add_column("Type", justify="center")
        table.add_column("Name", justify="left")
        table.add_column("Size", justify="center")
        table.add_column("Extension", justify="center")
        table.add_column("Resolution", justify="center")
        table.add_column("Duration", justify="center")
        for index, message in enumerate(matching_messages, start=1):
            file_info = {
                "type": "File",
                "name": None,
                "size": None,
                "extension": None,
                "resolution": None,
                "duration": None
            }
            if hasattr(message.file, "name") and message.file.name:
                file_info["name"] = message.file.name
                file_info["extension"] = os.path.splitext(message.file.name)[1].lower()
            else:
                file_info["name"] = f"File_{message.id}"
                file_info["extension"] = "Unknown"

            if hasattr(message.file, "size"):
                file_info["size"] = format_size(message.file.size)
            else:
                file_info["size"] = "Unknown size"

            if isinstance(message.media, types.MessageMediaPhoto):
                file_info["type"] = "Image"
                if hasattr(message.media, "photo") and hasattr(message.media.photo, "sizes"):
                    for size in message.media.photo.sizes:
                        if hasattr(size, "w") and hasattr(size, "h"):
                            file_info["resolution"] = f"{size.w}x{size.h}"
                            break

            elif isinstance(message.media, types.MessageMediaDocument):
                attributes = message.media.document.attributes
                if any(isinstance(attr, types.DocumentAttributeVideo) for attr in attributes):
                    file_info["type"] = "Video"
                    file_info["duration"] = get_video_duration(attributes)
                    for attr in attributes:
                        if isinstance(attr, types.DocumentAttributeVideo):
                            file_info["resolution"] = f"{attr.w}x{attr.h}"
                            break

            table.add_row(
                str(index),
                file_info["type"],
                shorten(file_info["name"], width=30, placeholder="..."),
                file_info["size"],
                file_info["extension"],
                file_info["resolution"] if file_info["resolution"] else "N/A",
                file_info["duration"] if file_info["duration"] else "N/A"
            )

        console.print(table)
        while True:
            choice = Prompt.ask(
                "Enter file numbers (e.g., '1,3,5'), 'all' to download all, or 'cancel' to skip",
                default="cancel"
            )
            if choice == "cancel":
                console.print("[yellow]Download cancelled.[/yellow]")
                return
            elif choice == "all":
                selected_indices = range(len(matching_messages))
                break
            else:
                try:
                    selected_indices = [int(idx.strip()) - 1 for idx in choice.split(",")]
                    if all(0 <= idx < len(matching_messages) for idx in selected_indices):
                        break
                    else:
                        console.print("[red]Invalid file numbers. Please try again.[/red]")
                except ValueError:
                    console.print("[red]Invalid input. Please enter numbers separated by commas.[/red]")

        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=console
        ) as progress:
            total_size = sum(message.file.size for message in [matching_messages[idx] for idx in selected_indices])
            overall_task = progress.add_task(f"[green]Downloading {len(selected_indices)} files ({format_size(total_size)})...", total=total_size)
            for idx in selected_indices:
                message = matching_messages[idx]
                current_file_name = message.file.name or f"File_{message.id}"
                file_size = message.file.size if message.file else 0
                file_size_str = format_size(file_size)

                if isinstance(message.media, types.MessageMediaPhoto):
                    media_type = "photo"
                elif isinstance(message.media, types.MessageMediaDocument):
                    if any(isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes):
                        media_type = "video"
                    else:
                        media_type = "document"
                else:
                    media_type = "file"

                task_id = progress.add_task(f"[cyan]Downloading {current_file_name} ({file_size_str})...", total=file_size)
                await download_media(message, downloaded_files, semaphore, media_type, progress, task_id)
                progress.update(overall_task, advance=file_size)

        console.print(f"[green]Download completed.[/green]")
    except Exception as e:
        logging.error(f"Error downloading file by name: {e}")
        console.print(f"[red]Error: {e}[/red]")

def display_detailed_timeline(detailed_timeline, title):
    if detailed_timeline:
        table = Table(title=title)
        table.add_column("Type", justify="center")
        table.add_column("Name", justify="left")
        table.add_column("Size", justify="center")
        table.add_column("Extension", justify="center")
        table.add_column("Resolution", justify="center")
        table.add_column("Duration", justify="center")
        for item in detailed_timeline:
            display_name = shorten(item["name"], width=30, placeholder="...")
            table.add_row(
                item["type"],
                display_name,
                item["size"],
                item["extension"],
                item["resolution"] if item["resolution"] else "N/A",
                item["duration"] if item["duration"] else "N/A"
            )

        console.print(table)
    else:
        console.print(f"[red]No media found.[/red]")

def display_file_type_menu(channel_name):
    console.clear()
    console.print(Panel.fit(
        Text(f"Downloading from: {channel_name}", style="bold blue"),
        border_style="green"
    ))
    menu_options = [
        ("1", "Download Media"),
        ("2", "Show media count"),
        ("3", "View Timeline"),
        ("4", "View Detailed Timeline"),
        ("5", "Search by File Size"),
        ("6", "Back to Main Menu"),
        ("7", "Exit")
    ]
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    for option, description in menu_options:
        menu_table.add_row(
            Text(option, style="bold yellow"),
            Text(description, style="cyan")
        )

    console.print(Panel(menu_table, title="File Type Menu", border_style="blue"))

def display_download_menu():
    console.clear()
    console.print(Panel.fit(
        Text("Download Media", style="bold blue"),
        border_style="green"
    ))
    menu_options = [
        ("1", "Download All Video"),
        ("2", "Download All Image"),
        ("3", "Download All File"),
        ("4", "Download by Name"),
        ("5", "Download by Date Range"),
        ("6", "Back to Previous Menu")
    ]
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    for option, description in menu_options:
        menu_table.add_row(
            Text(option, style="bold yellow"),
            Text(description, style="cyan")
        )

    console.print(Panel(menu_table, title="Download Menu", border_style="blue"))

async def search_by_size(channel_input, size_gb, search_type, tolerance=0.05, size_range=None):
    try:
        if not client.is_connected():
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=phone_number)

        size_bytes = size_gb * 1024 * 1024 * 1024
        tolerance_bytes = tolerance * 1024 * 1024 * 1024
        matching_messages = []
        async for message in client.iter_messages(channel_input):
            if message.media and hasattr(message.file, "size"):
                file_size = message.file.size
                if search_type == "less" and file_size < size_bytes:
                    matching_messages.append(message)
                elif search_type == "greater" and file_size > size_bytes:
                    matching_messages.append(message)
                elif search_type == "equal" and abs(file_size - size_bytes) <= tolerance_bytes:
                    matching_messages.append(message)
                elif search_type == "range" and size_range:
                    min_size_bytes = size_range[0] * 1024 * 1024 * 1024
                    max_size_bytes = size_range[1] * 1024 * 1024 * 1024
                    if min_size_bytes <= file_size <= max_size_bytes:
                        matching_messages.append(message)

        if not matching_messages:
            if search_type == "range":
                console.print(f"[yellow]No files found within the size range {size_range[0]} GB to {size_range[1]} GB.[/yellow]")
            else:
                console.print(f"[yellow]No files found with size {search_type} than {size_gb} GB.[/yellow]")
            return

        table = Table(title=f"Files with size {search_type} than {size_gb} GB" if search_type != "range" else f"Files within size range {size_range[0]} GB to {size_range[1]} GB")
        table.add_column("Type", justify="center")
        table.add_column("Name", justify="left")
        table.add_column("Size", justify="center")
        table.add_column("Extension", justify="center")
        table.add_column("Resolution", justify="center")
        table.add_column("Duration", justify="center")
        for message in matching_messages:
            file_info = {
                "type": "File",
                "name": None,
                "size": None,
                "extension": None,
                "resolution": None,
                "duration": None
            }
            if hasattr(message.file, "name") and message.file.name:
                file_info["name"] = message.file.name
                file_info["extension"] = os.path.splitext(message.file.name)[1].lower()
            else:
                file_info["name"] = f"File_{message.id}"
                file_info["extension"] = "Unknown"

            if hasattr(message.file, "size"):
                file_info["size"] = format_size(message.file.size)
            else:
                file_info["size"] = "Unknown size"

            if isinstance(message.media, types.MessageMediaPhoto):
                file_info["type"] = "Image"
                if hasattr(message.media, "photo") and hasattr(message.media.photo, "sizes"):
                    for size in message.media.photo.sizes:
                        if hasattr(size, "w") and hasattr(size, "h"):
                            file_info["resolution"] = f"{size.w}x{size.h}"
                            break

            elif isinstance(message.media, types.MessageMediaDocument):
                attributes = message.media.document.attributes
                if any(isinstance(attr, types.DocumentAttributeVideo) for attr in attributes):
                    file_info["type"] = "Video"
                    file_info["duration"] = get_video_duration(attributes)
                    for attr in attributes:
                        if isinstance(attr, types.DocumentAttributeVideo):
                            file_info["resolution"] = f"{attr.w}x{attr.h}"
                            break

            table.add_row(
                file_info["type"],
                shorten(file_info["name"], width=30, placeholder="..."),
                file_info["size"],
                file_info["extension"],
                file_info["resolution"] if file_info["resolution"] else "N/A",
                file_info["duration"] if file_info["duration"] else "N/A"
            )

        console.print(table)
        console.print(f"[green]Total files found: {len(matching_messages)}[/green]")
    except Exception as e:
        logging.error(f"Error searching by file size: {e}")
        console.print(f"[red]Error: {e}[/red]")

def display_size_search_menu():
    console.print(Panel.fit(
        Text("Search by File Size", style="bold blue"),
        border_style="green"
    ))
    menu_options = [
        ("1", "Find files smaller than specified size"),
        ("2", "Find files larger than specified size"),
        ("3", "Find files equal to specified size (with tolerance)"),
        ("4", "Find files within a size range"),
        ("5", "Back to Previous Menu ")
    ]
    menu_table = Table(show_header=False, box=None, padding=(0, 2))
    for option, description in menu_options:
        menu_table.add_row(
            Text(option, style="bold yellow"),
            Text(description, style="cyan")
        )

    console.print(Panel(menu_table, title="Size Search Menu", border_style="blue"))

async def list_all_chats_with_member_count():
    try:
        if not client.is_connected():
            await client.connect()
            if not await client.is_user_authorized():
                await client.start(phone=phone_number)

        dialogs = await client.get_dialogs()
        table = Table(title="All Chats/Channels/Groups")
        table.add_column("Chat Name", justify="left")
        table.add_column("Chat ID", justify="center")
        table.add_column("Last Message ID", justify="center")
        table.add_column("Type", justify="center")
        table.add_column("Member Count", justify="center")
        for dialog in dialogs:
            chat_name = dialog.name if hasattr(dialog, "name") else "Unknown"
            chat_id = dialog.id
            last_message_id = dialog.message.id if hasattr(dialog, "message") else "N/A"
            chat_type = "Channel" if dialog.is_channel else "Group" if dialog.is_group else "Private Chat"
            member_count = "N/A"
            if dialog.is_group or dialog.is_channel:
                try:
                    participants = await client.get_participants(dialog.entity)
                    member_count = len(participants)
                except Exception as e:
                    if dialog.is_channel and hasattr(dialog.entity, "participants_count"):
                        member_count = dialog.entity.participants_count
                    else:
                        logging.error(f"Error getting member count for chat {chat_id}: {e}")
                        console.print(f"[yellow]No permission to get member count for {chat_name}.[/yellow]")
                        member_count = "No Permission"

            table.add_row(
                chat_name,
                str(chat_id),
                str(last_message_id),
                chat_type,
                str(member_count)
            )

        console.print(table)
    except Exception as e:
        logging.error(f"Error listing chats: {e}")
        console.print(f"[red]Error: {e}[/red]")

async def download_by_chat_id(chat_id, media_type, start_date=None, end_date=None):
    if not client.is_connected():
        await client.connect()
        if not await client.is_user_authorized():
            await client.start(phone=phone_number)

    downloaded_files = get_downloaded_files()
    semaphore = asyncio.Semaphore(20)
    success_count = 0
    try:
        chat_entity = await client.get_entity(chat_id)
        messages = [
            message async for message in client.iter_messages(chat_entity)
            if message.media and (
                (media_type == "photo" and isinstance(message.media, types.MessageMediaPhoto)) or
                (media_type == "video" and isinstance(message.media, types.MessageMediaDocument) and
                 any(isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes)) or
                (media_type == "document" and isinstance(message.media, types.MessageMediaDocument) and
                 not any(isinstance(attr, types.DocumentAttributeVideo) for attr in message.media.document.attributes))
            )
        ]
        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, "%d/%m/%Y")
            end_date_obj = datetime.strptime(end_date, "%d/%m/%Y")
            messages = [
                message for message in messages
                if start_date_obj <= message.date.replace(tzinfo=None) <= end_date_obj
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
                    success_count += 1
                    progress.update(overall_task, advance=1)

        console.print(f"[green]Downloaded {success_count} {media_type}s out of {total_files}.[/green]")
    except Exception as e:
        logging.error(f"Error downloading {media_type}s: {e}")
        console.print(f"[red]Error downloading {media_type}s: {e}[/red]")

async def main():
    global accounts, client
    accounts = load_accounts()
    while True:
        display_main_menu()
        choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6", "7"])
        if choice in [1, 2, 3]:
            if not accounts:
                console.print("[red]No accounts found. Please add an account first.[/red]")
                continue

            account = accounts[current_account_index]
            client = TelegramClient(account["session_file"], account["api_id"], account["api_hash"])

            if choice == 1:
                channel_input = Prompt.ask("Enter the channel name")
            elif choice == 2:
                channel_input = Prompt.ask("Enter the invite link")
            elif choice == 3:
                chat_id_input = IntPrompt.ask("Enter the Chat ID")
                channel_input = chat_id_input

            while True:
                display_file_type_menu(channel_input)
                file_choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6", "7"])
                if file_choice == 1:
                    while True:
                        display_download_menu()
                        download_choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6"])
                        if download_choice == 6:
                            break
                        elif download_choice == 1:
                            await download_by_type(channel_input, "video")
                        elif download_choice == 2:
                            await download_by_type(channel_input, "photo")
                        elif download_choice == 3:
                            await download_by_type(channel_input, "document")
                        elif download_choice == 4:
                            file_name = Prompt.ask("Enter the file name to download")
                            await download_by_name(channel_input, file_name)
                        elif download_choice == 5:
                            media_type_choice = IntPrompt.ask(
                                "Download by Date Range Options:\n1. Video\n2. Image\n3. File\nEnter your choice", choices=["1", "2", "3"])
                            start_date = Prompt.ask("Enter the start date (DD/MM/YYYY)")
                            end_date = Prompt.ask("Enter the end date (DD/MM/YYYY)")
                            if media_type_choice == 1:
                                await download_by_type(channel_input, "video", start_date, end_date)
                            elif media_type_choice == 2:
                                await download_by_type(channel_input, "photo", start_date, end_date)
                            elif media_type_choice == 3:
                                await download_by_type(channel_input, "document", start_date, end_date)
                elif file_choice == 2:
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
                elif file_choice == 3:
                    timeline_choice = IntPrompt.ask(
                        "View Timeline Options:\n1. All Time\n2. Specific Date\n3. Date Range\nEnter your choice", choices=["1", "2", "3"])
                    if timeline_choice == 1:
                        console.print("[bold]Fetching timeline for all time...[/bold]")
                        timeline, channel_name = await get_timeline_overview(channel_input)
                        if timeline:
                            table = Table(title=f"Timeline for {channel_name} (All Time)")
                            table.add_column("Date", justify="center")
                            table.add_column("Videos", justify="center")
                            table.add_column("Images", justify="center")
                            table.add_column("Files", justify="center")
                            for date, counts in sorted(timeline.items()):
                                table.add_row(date, str(counts["videos"]), str(counts["images"]), str(counts["files"]))
                            console.print(table)
                        else:
                            console.print("[red]Unable to fetch timeline.[/red]")
                    elif timeline_choice == 2:
                        specific_date = Prompt.ask("Enter the date (DD/MM/YYYY)")
                        console.print(f"[bold]Fetching timeline for {specific_date}...[/bold]")
                        timeline, channel_name = await get_timeline_overview(channel_input, start_date=specific_date)
                        if timeline:
                            counts = timeline.get(specific_date, {"videos": 0, "images": 0, "files": 0})
                            table = Table(title=f"Timeline for {channel_name} on {specific_date}")
                            table.add_column("Videos", justify="center")
                            table.add_column("Images", justify="center")
                            table.add_column("Files", justify="center")
                            table.add_row(str(counts["videos"]), str(counts["images"]), str(counts["files"]))
                            console.print(table)
                        else:
                            console.print("[red]Unable to fetch timeline.[/red]")
                    elif timeline_choice == 3:
                        start_date = Prompt.ask("Enter the start date (DD/MM/YYYY)")
                        end_date = Prompt.ask("Enter the end date (DD/MM/YYYY)")
                        console.print(f"[bold]Fetching timeline from {start_date} to {end_date}...[/bold]")
                        timeline, channel_name = await get_timeline_overview(channel_input, start_date=start_date, end_date=end_date)
                        if timeline:
                            table = Table(title=f"Timeline for {channel_name} from {start_date} to {end_date}")
                            table.add_column("Date", justify="center")
                            table.add_column("Videos", justify="center")
                            table.add_column("Images", justify="center")
                            table.add_column("Files", justify="center")
                            for date, counts in sorted(timeline.items()):
                                table.add_row(date, str(counts["videos"]), str(counts["images"]), str(counts["files"]))
                            console.print(table)
                        else:
                            console.print("[red]Unable to fetch timeline.[/red]")
                elif file_choice == 4:
                    timeline_choice = IntPrompt.ask(
                        "View Detailed Timeline Options:\n1. All Time\n2. Specific Date\n3. Date Range\nEnter your choice", choices=["1", "2", "3"])
                    if timeline_choice == 1:
                        console.print("[bold]Fetching detailed timeline for all time...[/bold]")
                        detailed_timeline = await get_detailed_timeline(channel_input)
                        display_detailed_timeline(detailed_timeline, "Detailed Timeline for All Time")
                    elif timeline_choice == 2:
                        specific_date = Prompt.ask("Enter the date to search (DD/MM/YYYY)")
                        console.print(f"[bold]Fetching detailed timeline for {specific_date}...[/bold]")
                        detailed_timeline = await get_detailed_timeline(channel_input, start_date=specific_date)
                        display_detailed_timeline(detailed_timeline, f"Detailed Timeline for {specific_date}")
                    elif timeline_choice == 3:
                        start_date = Prompt.ask("Enter the start date (DD/MM/YYYY)")
                        end_date = Prompt.ask("Enter the end date (DD/MM/YYYY)")
                        console.print(f"[bold]Fetching detailed timeline from {start_date} to {end_date}...[/bold]")
                        detailed_timeline = await get_detailed_timeline(channel_input, start_date=start_date, end_date=end_date)
                        display_detailed_timeline(detailed_timeline, f"Detailed Timeline from {start_date} to {end_date}")
                elif file_choice == 5:
                    while True:
                        display_size_search_menu()
                        size_search_choice = IntPrompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5"])
                        if size_search_choice == 5:
                            break
                        elif size_search_choice == 1:
                            size_gb = float(Prompt.ask("Enter the file size in GB (e.g., 1 for 1GB)"))
                            await search_by_size(channel_input, size_gb, "less")
                        elif size_search_choice == 2:
                            size_gb = float(Prompt.ask("Enter the file size in GB (e.g., 1 for 1GB)"))
                            await search_by_size(channel_input, size_gb, "greater")
                        elif size_search_choice == 3:
                            size_gb = float(Prompt.ask("Enter the file size in GB (e.g., 1 for 1GB)"))
                            tolerance_percent = float(Prompt.ask("Enter the tolerance percentage (e.g., 5 for 5%)", default="5"))
                            tolerance = tolerance_percent / 100
                            await search_by_size(channel_input, size_gb, "equal", tolerance)
                        elif size_search_choice == 4:
                            min_size_gb = float(Prompt.ask("Enter the minimum file size in GB (e.g., 0.5 for 500MB)"))
                            max_size_gb = float(Prompt.ask("Enter the maximum file size in GB (e.g., 1.5 for 1.5GB)"))
                            await search_by_size(channel_input, 0, "range", size_range=(min_size_gb, max_size_gb))
                elif file_choice == 6:
                    break
                elif file_choice == 7:
                    console.print("[bold]Exiting the program.[/bold]")
                    return
        elif choice == 4:
            await list_all_chats_with_member_count()
        elif choice == 5:
            manage_api_config()
        elif choice == 6:
            await manage_accounts()
        elif choice == 7:
            console.print("[bold]Exiting the program.[/bold]")
            break
        else:
            console.print("[red]Invalid choice, please try again.[/red]")
    if client.is_connected():
            await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())