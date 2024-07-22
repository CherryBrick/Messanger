import asyncio
import logging
import os
import struct

from dotenv import load_dotenv
from socket import error as SocketError

import sessions
from urls import urls

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

to_monitor = []


def parsing_request(request):
    if not request:
        logging.error('No request for parsing.')
        return ''
    parsed_request = request.split()
    logging.info('Request parsed.')
    return parsed_request


async def method_allowed(parsed_request, writer):
    if not parsed_request:
        response = 'First element has to be HTTP Method.'
        logging.error(response)
        await send_message(str(response), writer)
        return False
    if parsed_request[0] not in ('GET', 'POST'):
        response = f'Method {parsed_request[0]} not allowed.'
        logging.error(response)
        await send_message(str(response), writer)
        return False
    logging.info('Method allowed.')
    return True


async def send_message(message, writer):
    try:
        header = struct.pack('!I', len(message))
        writer.write(header)
        writer.write(message.encode())
        await writer.drain()
        logging.info('Message sent to client.')
    except Exception as e:
        writer.write(f'Server-side error {e}'.encode())
        logging.error(f'{e}')
        await writer.drain()


async def send_all(message):
    try:
        for client in sessions.connected_clients:
            await send_message(message, client)
    except Exception as e:
        logging.error(f'{e}')


async def run(reader, writer):
    async def close_session(writer, e, addr):
        writer.close()
        await writer.wait_closed()
        logging.error(f'{e}')
        user_id = sessions.sessions.pop([addr])['user_id']
        sessions.sessions[user_id] = {'connected': False}

    addr = writer.get_extra_info('peername')
    logging.info(f'Accepted connection from {addr}')
    sessions.connected_clients.append(writer)

    while True:
        try:
            request = await reader.read(1024)

            if len(request) == 0:
                sessions.connected_clients.remove(writer)
                writer.close()
                await writer.wait_closed()
                logging.info(f'Connection closed from addr {addr}.')
                try:
                    user_id = sessions.sessions.pop(str(addr))['user_id']
                    sessions.sessions[user_id] = {'connected': False}
                except Exception as e:
                    logging.error(f'{e}')
                    logging.info('Waiting for request.')
                break

            logging.info('Client sent request.')
            decoded_request = request.decode()
            logging.info(f'Decoded request is {decoded_request}')

            try:
                parsed_request = parsing_request(decoded_request)
            except Exception as e:
                logging.error(f"Error parsing request: {e}")
                logging.info('Waiting for request.')
                continue

            if not parsed_request or not await method_allowed(parsed_request,
                                                              writer):
                logging.info('Waiting for request.')
                continue

            if not parsed_request[1] in urls:
                await send_message('Invalid command.', writer)
                logging.info('Waiting for request.')
                continue

            response = await urls[parsed_request[1]](parsed_request, str(addr))
            await send_message(response, writer)

            if sessions.messages_to_send:
                # time.sleep(6)
                await send_all(
                    str(sessions.messages_to_send.pop(0)))

        except (asyncio.CancelledError, SocketError,
                ConnectionResetError) as e:
            await close_session(writer, e, addr)
            break
        except Exception as e:
            logging.error(f'{e}')
            logging.info('Waiting for request.')
