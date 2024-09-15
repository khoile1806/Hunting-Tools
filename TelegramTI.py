import aiohttp
import asyncio
import logging
from telegram import Bot
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("TelegramTI.log"),
        logging.StreamHandler()
    ]
)

TELEGRAM_TOKEN = '7171385980:AAHts1yco75v-q3mvha4H4n6QZrUmffPGV4'
CHAT_ID = '6229763712'
URL = 'https://thehackernews.com/'

sent_articles = set()

async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                logging.error(f"Failed to retrieve articles: {response.status}")
                return None
            return await response.text()
    except Exception as e:
        logging.error(f"Error fetching HTML: {e}")
        return None

def parse_articles(html):
    soup = BeautifulSoup(html, 'html.parser')
    articles = []
    for item in soup.find_all('div', class_='body-post clear'):
        title = item.find('h2', class_='home-title').get_text(strip=True)
        link = item.find('a', class_='story-link')['href']
        summary = item.find('div', class_='home-desc').get_text(strip=True)
        date = item.find('span', class_='h-datetime').get_text(strip=True)
        if link not in sent_articles:
            articles.append((title, link, summary, date))
            sent_articles.add(link)
            logging.info(f"New article found: {title} - {link}")
    return articles

async def get_latest_articles(session):
    logging.info("Fetching latest articles from The Hacker News")
    html = await fetch_html(session, URL)
    if html is None:
        return []
    return parse_articles(html)

async def send_message_via_telegram(bot, message):
    for attempt in range(3):
        try:
            logging.info(f"Attempt {attempt + 1}: Sending message to Telegram: {message}")
            await bot.send_message(chat_id=CHAT_ID, text=message)
            logging.info("Message sent successfully")
            return
        except Exception as e:
            logging.error(f"Failed to send message on attempt {attempt + 1}: {e}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)

async def check_internet_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.google.com', timeout=10) as response:
                return response.status == 200
    except:
        return False

async def main():
    async with Bot(token=TELEGRAM_TOKEN) as bot:
        sleep_duration = 600  # Default to 10 minutes
        async with aiohttp.ClientSession() as session:
            while True:
                if not await check_internet_connection():
                    logging.error("No internet connection. Retrying in 1 minute.")
                    await asyncio.sleep(60)  # Retry after 1 minute
                    continue

                logging.info("Checking for new articles")
                articles = await get_latest_articles(session)
                tasks = [
                    send_message_via_telegram(
                        bot,
                        f"• Title: {title}\n• Date: {date}\n• Summary: {summary}\n• Link: {link}"
                    ) for title, link, summary, date in articles[:3]
                ]
                if tasks:
                    await asyncio.gather(*tasks)
                logging.info(f"Sleeping for {sleep_duration // 60} minutes")
                await asyncio.sleep(sleep_duration)

if __name__ == "__main__":
    logging.info("Starting bot")
    asyncio.run(main())