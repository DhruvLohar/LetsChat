import socket, json
from socket import AF_INET, SOCK_STREAM

class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.buff_size = 4096

        self.user, self.room = None, None

        self.server = socket.socket(AF_INET, SOCK_STREAM)
        self.server.connect((self.host, self.port))

    def join_room(self, username, room_id):
        self.server.send(json.dumps({
            'type': 'join_room',
            'username': username,
            'room_id': room_id
        }).encode())
        self.user, self.room = username, room_id

    def create_room(self, username, room_id, max_len):
        self.server.send(json.dumps({
            'type': 'create_room',
            'username': username,
            'room_id': room_id,
            'max_len': int(max_len)
        }).encode())
        self.user, self.room = username, room_id
    
    def send_message(self, msg):
        self.server.send(json.dumps({
            'type': 'message_in',
            'user': self.user,
            'room': self.room,
            'message': msg
        }).encode())
    
    def exit_server(self):
        self.server.send(json.dumps({
            'type': 'left_room',
            'user': self.user,
            'room': self.room
        }).encode())
        self.server.close()
