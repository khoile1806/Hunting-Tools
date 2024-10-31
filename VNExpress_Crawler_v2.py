import sys
import aiohttp
import asyncio
import logging
from telegram import Bot
from bs4 import BeautifulSoup

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("BaoTinTucBot.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

TELEGRAM_TOKEN = ''
CHAT_ID = ''
URL = "https://vnexpress.net/tin-tuc-24h"
sent_articles = set()

async def fetch_html(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status != 200:
                logging.error(f"Failed to retrieve data: {response.status}")
                return None
            return await response.text()
    except Exception as e:
        logging.error(f"Error fetching HTML: {e}")
        return None

def parse_articles(html):
    soup = BeautifulSoup(html, 'html.parser')
    articles = []

    for item in soup.find_all('article', class_='item-news'):
        title_tag = item.find('h3', class_='title-news')
        link_tag = item.find('a')

        if title_tag and link_tag:
            title = title_tag.get_text(strip=True)
            link = link_tag['href']

            summary_tag = item.find('p', class_='description')
            summary = summary_tag.get_text(strip=True) if summary_tag else "No summary available"

            if link not in sent_articles:
                articles.append((title, link, summary))
                sent_articles.add(link)
                logging.info(f"New article found: {title} - {link}")

    return articles

async def get_latest_articles(session):
    html = await fetch_html(session, URL)
    if html is None:
        return []
    return parse_articles(html)

async def send_message_via_telegram(bot, message):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode='HTML')
        logging.info("Message sent successfully")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

async def main():
    async with Bot(token=TELEGRAM_TOKEN) as bot:
        async with aiohttp.ClientSession() as session:
            while True:
                logging.info("Checking for new articles from VNExpress")
                articles = await get_latest_articles(session)

                tasks = [
                    send_message_via_telegram(
                        bot,
                        f"<b>Title:</b> {title}\n"
                        f"<b>Summary:</b> {summary}\n"
                        f"<b>Link:</b> {link}"
                    ) for title, link, summary in articles[:2]
                ]

                if tasks:
                    await asyncio.gather(*tasks)

                logging.info("Sleeping for 1 minutes before the next check")
                await asyncio.sleep(60)

if __name__ == "__main__":
    logging.info("Starting the bot")
    asyncio.run(main())