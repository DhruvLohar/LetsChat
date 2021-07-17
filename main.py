import kivy
from kivy.lang import Builder
from kivy.config import Config
from kivymd.app import MDApp
from kivymd.toast import toast
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivymd.uix.label import MDLabel
from kivy.uix.screenmanager import ScreenManager, Screen, CardTransition
from kivymd.uix.card import MDCard
from kivymd.uix.list import OneLineIconListItem, TwoLineListItem

import json
from threading import Thread
from core.handler.client import Client

Config.set('graphics', 'resizeable', False)
Config.write()

class Home(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
    
    username = ObjectProperty(None)
    room = ObjectProperty(None)
    participants = ObjectProperty(None)

    def create_room(self):
        app = MDApp.get_running_app()
        if not len(self.username.text) <= self.username.max_text_length:
            toast(text=f"Please shorten your username upto {self.username.max_text_length} characters")
        elif not len(self.room.text) <= self.room.max_text_length:
            toast(text=f"Please shorten your room name upto {self.room.max_text_length} characters")
        elif not len(self.participants.text) <= self.participants.max_text_length:
            toast(text=f"Please shorten your participants limit upto {self.participants.max_text_length} digits")
        elif not self.participants.text.isnumeric():
            toast(text="Participants limit must be numeric")
        else:
            app.client.create_room(self.username.text, self.room.text, self.participants.text)
            screen_manager.get_screen('chat').ids.room_name.text = f"Room Name : {self.room.text}"
            self.switch('chat')

    @staticmethod
    def switch(page):
        screen_manager.transition = CardTransition(direction="left")
        screen_manager.current = page

class ConnectRoom(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name

    username = ObjectProperty(None)
    room = ObjectProperty(None)

    def join_room(self):
        app = MDApp.get_running_app()
        if not len(self.username.text) <= self.username.max_text_length:
            toast(text=f"Please shorten your username upto {self.username.max_text_length} characters")
        elif not len(self.room.text) <= self.room.max_text_length:
            toast(text=f"Please shorten your room name upto {self.room.max_text_length} characters")
        else:
            app.client.join_room(self.username.text, self.room.text)
            screen_manager.get_screen('chat').ids.room_name.text = f"Room Name : {self.room.text}"
            self.switch('chat')

    @staticmethod
    def switch(page):
        screen_manager.transition = CardTransition(direction="right")
        screen_manager.current = page

class DisplayUser(OneLineIconListItem):
    icon = StringProperty()

class Message(MDCard):
    username = StringProperty()
    message = StringProperty()

class Chat(Screen):
    def __init__(self, name):
        super().__init__()
        self.name = name
        self.font_name = "[font=core/assests/font/Russco.ttf]{}[/font]"

    message = ObjectProperty(None)

    def on_enter(self):
        Thread(target=self.data_receiver, daemon=True).start()

    def add_user(self, users):
        current_users = [x.text for x in self.ids.user_list.children]
        for user in users:
            if not self.font_name.format(user) in current_users:
                self.ids.user_list.add_widget(
                    DisplayUser(icon='account', text=self.font_name.format(user))
                )

    def remove_user(self, username):
        for user in self.ids.user_list.children:
            if user.text == self.font_name.format(username):
                self.ids.user_list.remove_widget(user)

    def data_receiver(self):
        app = MDApp.get_running_app()
        while True:
            data = json.loads(app.client.server.recv(4096).decode())
            if data:
                if data['type'] == 'room_joined':
                    if app.client.user != data['user_joined']: toast(text=f"{data['user_joined']} joined the room")
                    print(data)
                    self.add_user(data['users'])
                elif data['type'] == 'room_joined_full':
                    toast(text=f"{data['user']} tried joining the room")
                elif data['type'] == 'room_created':
                    self.add_user(data['users'])
                elif data['type'] == 'room_left':
                    toast(text=f"{data['user']} left the room")
                    self.remove_user(data['user'])
                elif data['type'] == 'message_out':
                    self.add_message(data['message'], data['from'])

    def add_message(self, message, user):
        self.ids.messages.add_widget(
            TwoLineListItem(text=user, secondary_text=message)
        )

    def send_msg(self):
        app = MDApp.get_running_app()
        app.client.send_message(self.message.text)
        self.ids.Message.text = ""

    @staticmethod
    def switch(page):
        screen_manager.current = page

class PageManager(ScreenManager):
    pass

kv_file = Builder.load_file('style.kv')
screen_manager = PageManager()

class LetsChatApp(MDApp):
    primary_font = 'core/assests/font/Pacifico.ttf'
    secondary_font = 'core/assests/font/Russco.ttf'
    client = Client('192.168.0.104', 8888)

    def on_stop(self):
        self.client.exit_server()

    def build(self):
        Window.size = (414, 800)
        self.theme_cls.primary_palette = 'LightGreen'

        screens = [Home(name="home"), Chat(name="chat"), ConnectRoom(name="connect_room")]
        for screen in screens:
            screen_manager.add_widget(screen)
        screen_manager.current = 'chat'

        return screen_manager


if __name__ == "__main__":
    app = LetsChatApp()
    app.run()