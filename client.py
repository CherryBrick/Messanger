import datetime
import json
import logging
import os
import select
import socket
import struct
import threading

from dotenv import load_dotenv
from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.widgets import (Button, Footer, Header,
                             Input, Static)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

HOST = os.getenv('HOST')
PORT = os.getenv('PORT')

to_monitor = []
lock = threading.Lock()
user_id = ''
event_connect = threading.Event()


class ClientApp(App):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.client_socket = None
        self.message_area = None
        self.log_area = None
        self.messages = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield Container(
            Horizontal(
                VerticalScroll(
                    Static(id='message_area'),
                ),
                VerticalScroll(
                    Static(id='log_area', expand=True),
                ),
                Vertical(
                    Input(placeholder='Type your message here...', id='input'),
                    Horizontal(
                        Button('Send message', id='send_button'),
                        Button('Connect', id='connect_button'),
                        Button('Get unread messages', id='get_unread_button'),
                    ),
                    Horizontal(
                        Button('Clear chat', id='clear_chat_button'),
                        Button('Clear logs', id='clear_logs_button'),
                        id='bottom_bar'
                    ),
                )
            )
        )

    def on_mount(self) -> None:
        self.message_area = self.query_one('#message_area')
        self.message_area.update('')
        self.log_area = self.query_one('#log_area')
        self.log_area.update('')

    def on_input_submitted(self) -> None:
        request = f'POST /send public {user_id} ' + \
            self.query_one('#input').value
        self.send_request(request)
        self.query_one('#input').clear()

    def on_button_pressed(self, event) -> None:
        match event.button.id:
            case 'send_button':
                request = f'POST /send public {user_id} ' + \
                    self.query_one('#input').value
                self.send_request(request)
                self.query_one('#input').clear()
            case 'connect_button':
                event_connect.set()
                self.send_request('POST /connect')
            case 'get_unread_button':
                self.send_request(f'GET /unread public {user_id}')
            case 'clear_chat_button':
                self.message_area.update()
            case 'clear_logs_button':
                self.log_area.update()

    def update_message_area(self, message: str) -> None:
        self.message_area.update(self.message_area.renderable + '\n' + message)

    def update_log(self, log_message: str) -> None:
        self.log_area.update(self.log_area.renderable + '\n' + log_message)

    def send_request(self, request: str) -> None:
        try:
            if not to_monitor or not (self.client_socket in to_monitor):
                self.client_socket = socket_register()
            self.client_socket.sendall(request.encode())
            self.update_log(f'Sent: {request}')
        except Exception as e:
            self.update_log(f'Error app: {e}')

    def add_messages(self, received_messages):
        for item in received_messages:
            timestamp = datetime.datetime. \
                fromisoformat(item['timestamp']). \
                strftime('%Y-%m-%d %H:%M')
            detailed_message = (f'{timestamp}',
                                f' user_{item['user_id'][:4]}',
                                f' {item['message']}')
            self.messages.append(detailed_message)
        self.update_log('Messages added to storage.')

    def mark_read(self, received_messages):
        timestamps = '/'.join(item['timestamp'] for item in received_messages)
        request = f'POST /read {timestamps} {user_id} public'
        self.send_request(request)

    def print_messages(self, received_messages):
        if len(received_messages) == 1:
            self.update_message_area(self.messages[-1])
            self.update_log('Message printed.')
        else:
            self.messages.sort(key=lambda x: x[0])
            self.message_area.update()
            to_render = str()
            for message in self.messages:
                to_render += ' '.join(message)
                to_render += '\n'
            self.message_area.update(self.message_area.renderable + '\n' + to_render)
            self.update_log('Messages sorted and printed.')



def socket_register():
    server_address = (HOST, int(PORT))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(server_address)

    with lock:
        to_monitor.append(client_socket)
    return client_socket


def event_loop(app: ClientApp):
    while True:
        global user_id
        with lock:
            if not to_monitor:
                continue
            ready_to_read, _, _ = select.select(to_monitor, [], [])
        for sock in ready_to_read:
            try:
                buffer = sock.recv(4)
                app.update_log(f'Message byte len is {buffer}')
                msg_ln = struct.unpack('!I', buffer)[0]
                if not isinstance(msg_ln, int):
                    continue
                response = sock.recv(msg_ln)
                app.update_log(f'Response received. is {response}')
                if not response:
                    app.update_message_area('Server closed the connection.')
                    with lock:
                        to_monitor.remove(sock)
                    sock.close()
                    user_id = ''
                else:
                    response_message = response.decode()
                    app.update_log('Response decoded.')
                    response_dict = json.loads(response_message)
                    app.update_log('json parsed.')
                    if event_connect.is_set():
                        user_id = response_dict['user_id']
                        event_connect.clear()
                        app.update_log(f'user_id updated: {user_id}')
                    try:
                        app.update_message_area(f'{response_dict['status']}')
                    except KeyError:
                        pass
                    received_messages = response_dict['messages']
                    app.add_messages(received_messages)
                    app.print_messages(received_messages)
                    app.mark_read(received_messages)
            except Exception as e:
                app.update_log(f'Error: {e}')
                with lock:
                    to_monitor.remove(sock)
                    sock.close()
                    user_id = ''


def main():
    app = ClientApp()

    event_loop_thread = threading.Thread(target=event_loop, args=(app,))
    event_loop_thread.daemon = True
    event_loop_thread.start()

    app.run()


if __name__ == '__main__':
    main()
