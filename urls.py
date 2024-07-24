import json
import logging
import threading
import uuid

import messages_manager as mm

import sessions

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

lock = threading.Lock()


class PostConnection:
    allowed_methods = ['POST']

    @classmethod
    async def view(cls, parsed_request, addr, *args, **kwargs):
        if parsed_request[0] not in PostConnection.allowed_methods:
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


class GetStatus:
    allowed_methods = ['GET']

    @classmethod
    async def view(cls, parsed_request, *args, **kwargs):
        if parsed_request[0] not in GetStatus.allowed_methods:
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


class PostSend:
    allowed_methods = ['POST']

    @classmethod
    async def view(cls, parsed_request, *args, **kwargs):
        if parsed_request[0] not in PostSend.allowed_methods:
            return 'Wrong method.'
        chat_id, user_id, message = \
            parsed_request[2], parsed_request[3], ' '.join(parsed_request[4:]),
        if (user_id in sessions.sessions) and \
           (sessions.sessions[user_id]['connected']) and \
           (chat_id == 'public' or chat_id in sessions.sessions):
            message_data = mm.save_message_to_csv(message, user_id, chat_id)
            message_to_send = dict()
            message_to_send['timestamp'] = message_data[0]
            message_to_send['user_id'] = message_data[1]
            message_to_send['message'] = message_data[2]

            response = {'status': 'message sent',
                        'user_id': user_id,
                        }
            if chat_id == 'public':
                with lock:
                    sessions.messages_to_send.append(
                        json.dumps({'messages': [message_to_send]}))
                logging.info(f'Message \'{message}\' '
                             'appended to messages_to_send list.')
        else:
            response = {'status': 'user not connected',
                        'user_id': user_id,
                        }
        return str(json.dumps(response))


class PostMarkRead:
    allowed_methods = ['POST']

    @classmethod
    async def view(cls, parsed_request, *args, **kwargs):
        if parsed_request[0] not in PostMarkRead.allowed_methods:
            return 'Wrong method.'
        timestamps = parsed_request[2]
        user_id = parsed_request[3]
        chat_id = parsed_request[4]
        mm.update_message_status(timestamps, user_id, chat_id)
        return None


class GetUnread:
    allowed_methods = ['GET']

    @classmethod
    async def view(cls, parsed_request, *args, **kwargs):
        if parsed_request[0] not in GetUnread.allowed_methods:
            return 'Wrong method.'
        chat_id = parsed_request[2]
        user_id = parsed_request[3]
        if (user_id in sessions.sessions) and \
           (sessions.sessions[user_id]['connected']) and \
           (chat_id == 'public' or chat_id in sessions.sessions):
            unread_messages = mm.get_unread_messages(user_id, chat_id)
            if not unread_messages:
                response = {
                    'status': 'no unread messages',
                    'user_id': user_id,
                    'messages': unread_messages
                }
            else:
                response = {
                    'status': 'unread messages received',
                    'user_id': user_id,
                    'messages': unread_messages
                }
        else:
            response = {'status': 'user not connected',
                        'user_id': user_id,
                        }
        return str(json.dumps(response))


urls = {
        '/connect': PostConnection.view,
        '/status': GetStatus.view,
        '/send': PostSend.view,
        '/read': PostMarkRead.view,
        '/unread': GetUnread.view,
        }
