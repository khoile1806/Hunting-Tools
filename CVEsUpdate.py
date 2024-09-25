import time
import asyncio
import logging
import aiofiles
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
SENT_CVE_FILE = 'CVES_ID.txt'
DAILY_REPORT_FILE = 'daily_report.txt'

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

async def save_sent_cve_id(cve_id):
    async with aiofiles.open(SENT_CVE_FILE, 'a') as f:
        await f.write(f"{cve_id}\n")

async def fetch_latest_cves():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(CVE_API_URL, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientResponseError as e:
            logger.error(f"Client error fetching CVEs: {e}")
            return []
        except aiohttp.ClientConnectionError as e:
            logger.error(f"Connection error fetching CVEs: {e}")
            return []
        except asyncio.TimeoutError:
            logger.error("Timeout error fetching CVEs")
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
            cwe = cve.get('cwe', 'N/A')
            references = '\n'.join(cve.get('references', 'N/A'))
            published = cve.get('Published', 'N/A')

            message = (
                f"• CVE ID: {cve_id}\n"
                f"• CWE: {cwe}\n"
                f"• Published: {published}\n"
                f"• Summary: {summary}\n"
                f"• References: {references}\n"
            )
            tasks.append(asyncio.create_task(send_telegram_message(bot, CHAT_ID, message)))
            sent_cve_ids.add(cve_id)
            await save_sent_cve_id(cve_id)
            await save_daily_report(cve_id, summary, cwe, published, references)
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

async def save_daily_report(cve_id, summary, cwe, published, references):
    async with aiofiles.open(DAILY_REPORT_FILE, 'a') as f:
        await f.write(
            f"• CVE ID: {cve_id}\n"
            f"• CWE: {cwe}\n"
            f"• Published: {published}\n"
            f"• Summary: {summary}\n"
            f"• References: {references}\n"
        )

async def send_daily_report(bot):
    try:
        async with aiofiles.open(DAILY_REPORT_FILE, 'r') as f:
            report = await f.read()
        cve_count = report.count('• CVE ID:')
        if cve_count > 0:
            await send_telegram_message(bot, CHAT_ID, f"Number of CVEs found today: {cve_count}")
        else:
            await send_telegram_message(bot, CHAT_ID, "No CVEs found today.")
    except FileNotFoundError:
        await send_telegram_message(bot, CHAT_ID, "No CVEs found today.")
    finally:
        async with aiofiles.open(DAILY_REPORT_FILE, 'w') as f:
            await f.truncate(0)

async def check_internet_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.google.com', timeout=10) as response:
                return response.status == 200
    except:
        return False

async def main():
    async with Bot(token=TELEGRAM_TOKEN) as bot:
        sent_cve_ids = load_sent_cve_ids()
        while True:
            try:
                if not await check_internet_connection():
                    logger.error("No internet connection.")
                    await send_telegram_message(bot, CHAT_ID, "No internet connection.")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                start_time = time.time()
                logger.info("Starting CVE check")

                cves = await fetch_latest_cves()
                await process_cves(bot, cves, sent_cve_ids)

                end_time = time.time()
                logger.info(f"Finished CVE check in {end_time - start_time:.2f} seconds")

                await asyncio.sleep(CHECK_INTERVAL)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                await send_telegram_message(bot, CHAT_ID, f"Unexpected error: {e}")
                await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    logging.info("Starting bot")
    asyncio.run(main())