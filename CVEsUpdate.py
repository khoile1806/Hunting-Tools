import time
import asyncio
import logging
import aiohttp
from telegram import Bot
from telegram.error import TelegramError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("CVES.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = ''
CHAT_ID = ''
CVE_API_URL = 'https://cve.circl.lu/api/last'
CHECK_INTERVAL = 600
sent_cve_ids = set()
SENT_CVE_FILE = 'CVES_ID.txt'

async def send_telegram_message(bot, chat_id, message, retries=3):
    for attempt in range(retries):
        try:
            await bot.send_message(chat_id=chat_id, text=message)
            logger.info(f"Sent message: {message}")
            return
        except TelegramError as e:
            logger.error(f"Error sending message: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                logger.error("Max retries reached. Failed to send message.")

def load_sent_cve_ids():
    try:
        with open(SENT_CVE_FILE, 'r') as f:
            return set(line.strip() for line in f)
    except FileNotFoundError:
        return set()

def save_sent_cve_id(cve_id):
    with open(SENT_CVE_FILE, 'a') as f:
        f.write(f"{cve_id}\n")
async def fetch_latest_cves():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(CVE_API_URL) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"Client error fetching CVEs: {e}")
            return []
        except aiohttp.ClientConnectionError as e:
            logger.error(f"Connection error fetching CVEs: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error fetching CVEs: {e}")
            return []

async def process_cves(bot, cves, sent_cve_ids):
    tasks = []
    for cve in cves:
        cve_id = cve.get('id')
        if cve_id and cve_id not in sent_cve_ids:
            summary = cve.get('summary', 'No summary available')
            message = f"CVE ID: {cve_id}\nSummary: {summary}"
            tasks.append(asyncio.create_task(send_telegram_message(bot, CHAT_ID, message)))
            sent_cve_ids.add(cve_id)
            save_sent_cve_id(cve_id)
    if tasks:
        await asyncio.gather(*tasks)
async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    sent_cve_ids = load_sent_cve_ids()
    while True:
        try:
            start_time = time.time()
            logger.info("Starting CVE check")

            cves = await fetch_latest_cves()
            await process_cves(bot, cves, sent_cve_ids)

            end_time = time.time()
            logger.info(f"Finished CVE check in {end_time - start_time:.2f} seconds")

            await asyncio.sleep(CHECK_INTERVAL)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logging.info("Starting bot")
    asyncio.run(main())