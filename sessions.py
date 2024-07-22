from multiprocessing import Manager

manager = Manager()
connected_clients = []
messages_to_send = manager.list()
sessions = manager.dict()
