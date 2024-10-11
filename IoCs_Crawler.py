import time
import html
import json
import logging
import requests
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("IoCs_Crawler.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = ''
TELEGRAM_CHAT_ID = ''
THREATFOX_API_URL = 'https://threatfox-api.abuse.ch/api/v1/'
IOC_FILE = 'ioc_list.txt'

def read_ioc_file():
    ioc_path = Path(IOC_FILE)
    if not ioc_path.is_file():
        return set()
    with ioc_path.open('r') as file:
        return set(line.strip() for line in file)

def write_ioc_file(ioc_set):
    with Path(IOC_FILE).open('w') as file:
        for ioc in ioc_set:
            file.write(f"{ioc}\n")

def get_ioc_data():
    payload = {'query': 'get_iocs', 'limit': 5}
    try:
        response = requests.post(THREATFOX_API_URL, data=json.dumps(payload))
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch IoC data: {e}")
        return None

def send_message_to_telegram(bot_token, chat_id, message):
    if not message:
        logging.error("Message text is empty, not sending")
        return None
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': html.escape(message),
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to send message to Telegram: {e}")
        return None

def check_for_new_iocs():
    known_iocs = read_ioc_file()
    ioc_data = get_ioc_data()
    if ioc_data and 'data' in ioc_data:
        new_iocs = set()
        for ioc in ioc_data['data']:
            ioc_value = ioc.get('ioc')
            ioc_type = ioc.get('ioc_type', 'N/A')
            malware = ioc.get('malware', 'N/A')
            first_seen = ioc.get('first_seen', 'N/A')

            if ioc_value and ioc_value not in known_iocs:
                message = (f"New IoC Detected:\n\n"
                           f"Type: {html.escape(ioc_type)}\n"
                           f"Value: {html.escape(ioc_value)}\n"
                           f"Description: {html.escape(malware)}\n"
                           f"First Seen: {html.escape(first_seen)}")
                logging.info(f"Generated message: {message}")

                response = send_message_to_telegram(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, message)
                if response and response.status_code == 200:
                    logging.info("Message sent successfully")
                    new_iocs.add(ioc_value)
                else:
                    logging.error("Failed to send message")
        known_iocs.update(new_iocs)
        write_ioc_file(known_iocs)
    else:
        logging.error("No IoC data available or failed to fetch IoC data")

def main():
    while True:
        check_for_new_iocs()
        time.sleep(300)

if __name__ == "__main__":
    main()
