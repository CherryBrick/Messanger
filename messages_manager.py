import csv
import logging
import os

from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

CHAT_LOG_DIR = os.getenv('CHAT_LOG_DIR')
os.makedirs(CHAT_LOG_DIR, exist_ok=True)


def save_message_to_csv(message: str, user_id: str,
                        chat_id: str = 'public'):
    chat_log_file = os.path.join(CHAT_LOG_DIR, f'{chat_id}.csv')
    message_data = [datetime.now().isoformat(), user_id, message]

    try:
        file_exists = os.path.isfile(chat_log_file)

        with open(chat_log_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['timestamp', 'user_id', 'message'])
            writer.writerow(message_data)
            logging.info(f'Message saved to {chat_log_file}.')
        return message_data
    except Exception as e:
        logging.error(f'Error saving message to csv: {e}')


def get_latest_messages(chat_id: str, limit: int = 20):
    chat_log_file = os.path.join(CHAT_LOG_DIR, f'{chat_id}.csv')
    messages = []
    if os.path.isfile(chat_log_file):
        with open(chat_log_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            messages = list(reader)[-limit:]
    return messages
