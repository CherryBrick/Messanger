import asyncio
import logging
import os

# from functools import wraps
from dotenv import load_dotenv

import messages_manager as mm

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')
CHAT_LOG_DIR = os.getenv('CHAT_LOG_DIR')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

to_monitor = []


# def generator_init(func):
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         gen = func(*args, **kwargs)
#         gen.send(None)
#         return gen
#     return wrapper


async def parsing_request(request):
    if not request:
        logging.error('No request for parsing.')
        return ''
    parsed_request = request.split()
    logging.info('Request parsed.')
    return parsed_request


# def method_allowed(parsed_request):
#     if not parsed_request:
#         return False
#     if parsed_request[0] != 'GET':
#         logging.error(f'Method {parsed_request[0]} not allowed.')
#         return False
#     logging.info('Method GET allowed.')
#     return True


# @generator_init
# def generate_response():
#     responses = ['Один запрос', 'Второй запрос', 'Третий запрос']
#     logging.info('Response generator initialized.')
#     while True:
#         for response in responses:
#             while True:
#                 try:
#                     logging.info('Waiting for request.\n')
#                     parsed_request = yield
#                     if len(parsed_request) < 2:
#                         logging.error('Request must contain \'<METHOD>'
#                                       ' <MESSAGE>.\'')
#                         yield b'Request must contain \'<METHOD> <MESSAGE>.\'\n'
#                         continue
#                     if not method_allowed(parsed_request):
#                         yield b'Method not allowed.\n'
#                         continue
#                     client_response = response + ' ' + ' '.join(
#                         word for word in parsed_request[1:]) + '\n'
#                     logging.info(f'Response is {client_response}')
#                     encoded_response = client_response.encode()
#                     logging.info('Response is encoded.')
#                     yield encoded_response
#                     break
#                 except Exception as e:
#                     logging.error(f'{e}')
#                     yield f'Response generating error: {e}\n'.encode()


async def send_message(message, writer):
    try:
        writer.write(writer)
        await writer.drain()
        logging.info('Message sent to clients.')
    except Exception as e:
        writer.write(f'Server-side error {e}'.encode())
        logging.error(f'{e}')
        await writer.drain()


async def run(reader, writer):
    # chat_log_file = os.path.join(CHAT_LOG_DIR, 'public.csv')
    # TODO: sent latest 20 messages on connection
    addr = writer.get_extra_info('peername')
    logging.info(f'Accepted connection from {addr}')
    while True:
        try:
            request = await reader.read(1024)
            if len(request) == 0:
                writer.close()
                await writer.wait_closed()
                logging.info('Connection closed.')
                break
            if request:
                logging.info('Client sent request.')
                decoded_request = request.decode()
                logging.info(f'Decoded request is {decoded_request}')
                parsed_request = await parsing_request(decoded_request)
                if parsed_request != '':
                    message = ' '.join(word for word in parsed_request)
                    await mm.save_message_to_csv(message)
            else:
                logging.error('Empty request.')
                logging.info('Waiting for request.')
        except asyncio.CancelledError:
            writer.close()
            await writer.wait_closed()
            logging.info('Connection closed.')
            break
