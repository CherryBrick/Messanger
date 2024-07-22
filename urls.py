import json
import logging
import uuid

import messages_manager as mm

import sessions

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')


class Post_connection():
    allowed_methods = ['POST']

    @classmethod
    async def view(cls, parsed_request, addr, *args, **kwargs):
        if parsed_request[0] not in Post_connection.allowed_methods:
            return 'Wrong method.'
        user_id = str(uuid.uuid4())
        sessions.sessions[user_id] = {'connected': True}
        sessions.sessions[addr] = {'user_id': user_id}
        logging.info(f'User {user_id} connected on {addr}.')
        latest_messages = mm.get_latest_messages('public')
        logging.info('Latest messages loaded.')
        response = {
            'status': 'connected',
            'user_id': user_id,
            'messages': latest_messages
        }
        return str(json.dumps(response))


class Get_status():
    allowed_methods = ['GET']

    @classmethod
    async def view(cls, parsed_request, *args, **kwargs):
        if parsed_request[0] not in Get_status.allowed_methods:
            return 'Wrong method.'
        user_id = parsed_request[2]
        if user_id in sessions.sessions and \
                sessions.sessions[user_id]['connected']:
            response = {'status': 'connected',
                        'user_id': user_id,
                        }
        else:
            response = {'status': 'not connected',
                        'user_id': user_id,
                        }
        return str(json.dumps(response))


class Post_send():
    allowed_methods = ['POST']

    @classmethod
    async def view(cls, parsed_request, *args, **kwargs):
        if parsed_request[0] not in Post_send.allowed_methods:
            return 'Wrong method.'
        chat_id, user_id, message = \
            parsed_request[2], parsed_request[3], ' '.join(parsed_request[4:]),
        if (user_id in sessions.sessions) and \
           (sessions.sessions[user_id]['connected']) and \
           (chat_id == 'public' or chat_id in sessions.sessions):
            message_data = mm.save_message_to_csv(message, user_id, chat_id)
            message_to_send = {}
            message_to_send['timestamp'] = message_data[0]
            message_to_send['user_id'] = message_data[1]
            message_to_send['message'] = message_data[2]

            response = {'status': 'message sent',
                        'user_id': user_id,
                        }
            if chat_id == 'public':
                sessions.messages_to_send.append(
                    json.dumps({'messages': [message_to_send]}))
                logging.info(f'Message \'{message}\' '
                             'appended to messages_to_send list.')
        else:
            response = {'status': 'user not connected',
                        'user_id': user_id,
                        }
        return str(json.dumps(response))


urls = {
        '/connect': Post_connection.view,
        '/status': Get_status.view,
        '/send': Post_send.view,
        }
