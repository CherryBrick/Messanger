import csv
import logging
import os
import threading

from datetime import datetime
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

CHAT_LOG_DIR = os.getenv('CHAT_LOG_DIR')
os.makedirs(CHAT_LOG_DIR, exist_ok=True)

lock = threading.Lock()


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


def update_message_status(timestamps: str, user_id: str, chat_id: str = 'public'):
    status_file = os.path.join(CHAT_LOG_DIR, f'{chat_id}_statuses.csv')
    timestamp_list = timestamps.split('/')
    updated_statuses = {}

    if os.path.isfile(status_file):
        with open(status_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            updated_statuses = list(reader)

    for timestamp in timestamp_list:
        found = False
        for status in updated_statuses:
            if status['timestamp'] == timestamp and status['user_id'] == user_id:
                found = True
                break
        if not found:
            updated_statuses.append({'timestamp': timestamp, 'user_id': user_id})

    try:
        with open(status_file, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['timestamp', 'user_id'])
            writer.writeheader()
            writer.writerows(updated_statuses)
    except Exception as e:
        logging.error(f'Error updating message status: {e}')


def get_unread_messages(user_id: str, chat_id: str = 'public'):
    chat_log_file = os.path.join(CHAT_LOG_DIR, f'{chat_id}.csv')
    status_file = os.path.join(CHAT_LOG_DIR, f'{chat_id}_statuses.csv')

    unread_messages = []
    if os.path.isfile(chat_log_file):
        with open(chat_log_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            all_messages = list(reader)
    else:
        logging.error(f'No chat log file found for chat_id {chat_id}.')
        return unread_messages

    read_statuses = []
    if os.path.isfile(status_file):
        with open(status_file, mode='r', newline='') as file:
            reader = csv.DictReader(file)
            read_statuses = list(reader)
            print(read_statuses)

    read_message_timestamps = {status['timestamp'] for status in read_statuses if user_id in status['user_id']}
    for message in all_messages:
        if message['timestamp'] not in read_message_timestamps:
            unread_messages.append(message)

    logging.info(f'Found {len(unread_messages)} unread messages for user {user_id}.')
    return unread_messages
