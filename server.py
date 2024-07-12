import logging
import os
import time

from functools import wraps
from dotenv import load_dotenv
from select import select

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

to_monitor = []


def generator_init(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        gen = func(*args, **kwargs)
        gen.send(None)
        return gen
    return wrapper


def parsing_request(request):
    if not request:
        logging.error('No request for parsing.')
        return ''
    parsed_request = request.split()
    logging.info('Request parsed.')
    return parsed_request


def method_allowed(parsed_request):
    if not parsed_request:
        return False
    if parsed_request[0] != 'GET':
        logging.error(f'Method {parsed_request[0]} not allowed.')
        return False
    logging.info('Method GET allowed.')
    return True


@generator_init
def generate_response():
    responses = ['Один запрос', 'Второй запрос', 'Третий запрос']
    logging.info('Response generator initialized.')
    while True:
        for response in responses:
            while True:
                try:
                    logging.info('Waiting for request.\n')
                    request = yield
                    parsed_request = parsing_request(request)
                    if len(parsed_request) < 2:
                        logging.error('Request must contain \'<METHOD>'
                                      ' <MESSAGE>.\'')
                        yield b'Request must contain \'<METHOD> <MESSAGE>.\'\n'
                        continue
                    if not method_allowed(parsed_request):
                        yield b'Method not allowed.\n'
                        continue
                    client_response = response + ' ' + ' '.join(
                        word for word in parsed_request[1:]) + '\n'
                    logging.info(f'Response is {client_response}')
                    encoded_response = client_response.encode()
                    logging.info('Response is encoded.')
                    yield encoded_response
                    break
                except Exception as e:
                    logging.error(f'{e}')
                    yield f'Response generating error: {e}\n'.encode()


def accept_connection(server_socket):
    client_socket, addr = server_socket.accept()
    logging.info(f'Client {addr} set up connection.')
    to_monitor.append(client_socket)
    logging.info(f'Client {addr} registered to monitor.')


def send_message(client_socket, response_generator):
    request = client_socket.recv(1024)
    time.sleep(5)
    if len(request) == 0:
        logging.info('Connection closed by client.')
        client_socket.close()
        to_monitor.remove(client_socket)
        logging.info('Waiting for request.')
    elif request:
        try:
            logging.info('Client sent request.')
            decoded_request = request.decode()
            logging.info(f'Decoded request is {decoded_request}')
            if decoded_request in ('quit\n', 'quit'):
                to_monitor.remove(client_socket)
                client_socket.sendall('Connection closed'.encode())
                client_socket.close()
                logging.info('Connection closed.')
                next(response_generator)
            else:
                generated_response = response_generator.send(
                    decoded_request)
                logging.info('Response generated.')
                client_socket.sendall(generated_response)
                logging.info('Response sent to client.')
        except Exception as e:
            client_socket.sendall(f'Server-side error: {e}'.encode())
            logging.error(f'{e}')
            to_monitor.remove(client_socket)
            client_socket.sendall('Connection closed'.encode())
            client_socket.close()
            logging.info('Connection closed.')
        finally:
            next(response_generator)
    else:
        logging.error('Empty request.')


def run(server_socket):
    to_monitor.append(server_socket)
    response_generator = generate_response()
    while True:
        ready_to_read, _, _ = select(to_monitor, [], [])
        for sock in ready_to_read:
            if sock is server_socket:
                accept_connection(sock)
            else:
                send_message(sock, response_generator)
