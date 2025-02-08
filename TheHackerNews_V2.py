import logging
import asyncio
import feedparser
from telegram import Bot
from deep_translator import GoogleTranslator

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

TELEGRAM_TOKEN = ''
CHAT_ID = ''
RSS_URL = 'https://feeds.feedburner.com/TheHackersNews'

sent_articles = set()

async def fetch_rss():
    logging.info("Fetching RSS feed")
    feed = feedparser.parse(RSS_URL)
    if feed.bozo:
        logging.error("Failed to parse RSS feed")
        return []
    articles = []
    for entry in feed.entries[:5]:
        if entry.link not in sent_articles:
            articles.append({
                'title': entry.title,
                'link': entry.link,
                'summary': entry.summary,
                'published': entry.published
            })
            sent_articles.add(entry.link)
    return articles

async def translate_text(text, dest_language="vi"):
    try:
        translated = GoogleTranslator(source="auto", target=dest_language).translate(text)
        return translated
    except Exception as e:
        logging.error(f"Translation error: {e}")
        return text

async def send_message_via_telegram(bot, article):
    translated_summary = await translate_text(article["summary"])
    message = (
        f"• *Title:* {article['title']}\n"
        f"• *Published:* {article['published']}\n"
        f"• *Summary (VN):* {translated_summary}\n"
        f"• *Link:* {article['link']}"
    )
    try:
        logging.info(f"Sending message to Telegram")
        await bot.send_message(chat_id=CHAT_ID, text=message, parse_mode="Markdown")
        logging.info("Message sent successfully")
    except Exception as e:
        logging.error(f"Failed to send message: {e}")


async def main():
    async with Bot(token=TELEGRAM_TOKEN) as bot:
        while True:
            articles = await fetch_rss()
            if articles:
                for article in articles:
                    await send_message_via_telegram(bot, article)
            else:
                logging.info("No new articles found")
            logging.info("Sleeping for 10 minutes")
            await asyncio.sleep(600)

if __name__ == "__main__":
    logging.info("Starting bot")
    asyncio.run(main())