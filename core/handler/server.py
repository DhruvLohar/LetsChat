import socket
import json
from threading import Thread
from socket import AF_INET, SOCK_STREAM, SO_REUSEADDR, SOL_SOCKET

class Server:
    def __init__(self, host, port, backlog):
        self.host = host
        self.port = port
        self.buff_size = 4069
        self.backlog = backlog

        self.rooms = {}
        self.users = {}

        self.server = socket.socket(AF_INET, SOCK_STREAM)
        self.server.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.server.bind((self.host, self.port))
        self.init_server()
    
    def boardcast(self, room, cast_type, data_to_emit=None):
        for user in self.rooms[room]['users']:
            conn = self.users[user]
            if cast_type == 'room_joined':
                conn.send(json.dumps({
                    'type': cast_type,
                    'users': self.rooms[room]['users'],
                    'user_joined': data_to_emit
                }).encode())
            elif cast_type == 'room_joined_full':
                conn.send(json.dumps({
                    'type': cast_type,
                    'user': data_to_emit
                }).encode())
            elif cast_type == 'room_created':
                conn = self.users[data_to_emit]
                conn.send(json.dumps({
                    'type': cast_type,
                    'users': self.rooms[room]['users']
                }).encode())
            elif cast_type == 'room_left':
                conn.send(json.dumps({
                    'type': cast_type,
                    'user': data_to_emit
                }).encode())
            elif cast_type == 'message_out':
                conn.send(json.dumps({
                    'type': cast_type,
                    'from': data_to_emit['user'],
                    'message': data_to_emit['message']
                }).encode())

    def join_room(self, data, conn):
        username, room_id = data['username'], data['room_id']
        self.users[username] = conn

        if room_id in self.rooms.keys():
            if len(self.rooms[room_id]['users']) >= self.rooms[room_id]['max_len']:
                self.boardcast(room_id, 'room_joined_full', username)
            else:
                self.rooms[room_id]['users'].append(username)
                self.boardcast(room_id, 'room_joined', username)
            Thread(target=self.client_handler, args=(conn, username,), daemon=True).start()

    def create_room(self, data, conn):
        username, room_id = data['username'], data['room_id']
        self.users[username] = conn

        if not room_id in self.rooms.keys():
            self.rooms[room_id] = {}
            self.rooms[room_id]['users'] = []
            self.rooms[room_id]['max_len'] = data['max_len']
            self.rooms[room_id]['users'].append(username)
            self.boardcast(room_id, 'room_created', username)
            Thread(target=self.client_handler, args=(conn, username,), daemon=True).start()

    def client_handler(self, conn, username):
        while True:
            data = json.loads(conn.recv(self.buff_size).decode())
            if data['type'] == 'left_room':
                self.rooms[data['room']]['users'].remove(data['user'])
                self.boardcast(data['room'], 'room_left', data['user'])
            elif data['type'] == 'message_in':
                self.boardcast(data['room'], 'message_out', data)

    def init_server(self):
        self.server.listen(self.backlog)
        print('listening ...')
        while True:
            conn, addr = self.server.accept()
            data = json.loads(conn.recv(self.buff_size).decode())
            if data['type'] == 'join_room':
                self.join_room(data, conn)
            elif data['type'] == 'create_room':
                self.create_room(data, conn)
            print(self.rooms)

server = Server('192.168.0.104', 8888, 10)

"""
rooms = {
    'room 1': {
        'users': [
            {
                'username': 'dhruv'
            },
            {
                'username': 'bhavesh'
            }
        ],
        'max_len': 2
    }
}
"""