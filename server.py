import logging
import os
import subprocess

from functools import wraps
from dotenv import load_dotenv

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


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
                        yield b'Request must contain \'<METHOD> <MESSAGE>.\''
                        continue
                    if not method_allowed(parsed_request):
                        yield b'Method not allowed.'
                        continue
                    client_response = response + ' ' + ' '.join(
                        word for word in parsed_request[1:])
                    logging.info(f'Response is {client_response}.')
                    encoded_response = client_response.encode()
                    logging.info('Response is encoded.')
                    yield encoded_response
                    break
                except Exception as e:
                    logging.error(f'{e}')
                    yield f'Response generating error: {e}'.encode()


def run(response_generator, server_socket):
    try:
        client_socket, addr = server_socket.accept()
        logging.info(f'Client {addr} set up connection.')
        request = client_socket.recv(1024)
        if request:
            try:
                logging.info('Client sent request.')
                decoded_request = request.decode()
                logging.info(f'Decoded request is {decoded_request}.')
                generated_response = response_generator.send(
                    decoded_request)
                logging.info('Response generated.')
                client_socket.sendall(generated_response)
                logging.info('Response sent to client.')
            except Exception as e:
                client_socket.sendall(f'Server-side error: {e}'.encode())
                logging.error(f'{e}')
                client_socket.close()
                logging.info('Connection closed.')
            finally:
                client_socket.close()
                logging.info('Connection closed.')
                next(response_generator)
        else:
            logging.error('Empty request.')
            logging.info('Waiting for request.\n')
    except KeyboardInterrupt:
        try:
            client_socket.close()
            logging.info('Connection closed.')
        finally:
            subprocess.run(['npx', 'kill-port', PORT])
