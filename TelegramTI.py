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

TELEGRAM_TOKEN = ''
CHAT_ID = ''
URL = 'https://thehackernews.com/'

sent_articles = set()

async def get_latest_articles():
    logging.info("Fetching latest articles from The Hacker News")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(URL) as response:
                if response.status != 200:
                    logging.error(f"Failed to retrieve articles: {response.status}")
                    return []

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                articles = []
                for item in soup.find_all('div', class_='body-post clear'):
                    title = item.find('h2', class_='home-title').get_text(strip=True)
                    link = item.find('a', class_='story-link')['href']
                    if link not in sent_articles:
                        articles.append((title, link))
                        sent_articles.add(link)
                        logging.info(f"New article found: {title} - {link}")

                return articles
        except Exception as e:
            logging.error(f"Error fetching articles: {e}")
            return []

async def send_message_via_telegram(bot, message):
    try:
        logging.info(f"Sending message to Telegram: {message}")
        await bot.send_message(chat_id=CHAT_ID, text=message)
    except Exception as e:
        logging.error(f"Failed to send message: {e}")

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    sleep_duration = 600  # Default to 10 minutes
    while True:
        logging.info("Checking for new articles")
        articles = await get_latest_articles()
        tasks = [send_message_via_telegram(bot, f"{title}\n{link}") for title, link in articles[:10]]
        if tasks:
            await asyncio.gather(*tasks)
        logging.info(f"Sleeping for {sleep_duration // 60} minutes")
        await asyncio.sleep(sleep_duration)

if __name__ == "__main__":
    logging.info("Starting bot")
    asyncio.run(main())