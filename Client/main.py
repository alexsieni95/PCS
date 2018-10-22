from client import Client
from PIL import ImageTk, Image
from Chat import ChatGUI
from Login import LoginGUI
from SignUp import SignUpGUI
import os
import ctypes
import sys

host = '10.102.11.147'
port = 6000
MESSAGE = 'hi'

if os.getcwd().find("Client") == -1:
    os.chdir("Client")

if sys.platform.startswith('win'):
        ctypes.windll.shcore.SetProcessDpiAwareness(1)

chat = ChatGUI()
chat.withdraw()
login = LoginGUI()
signUp = SignUpGUI()
signUp.withdraw()
client = Client(host, port, chat.activeChat)
chat.createWidgets(client)
client.connectServer()

login.setSignUpWindow(signUp)
login.setItems(client, chat)
signUp.setLoginWindow(login)
signUp.setClient(client)

chat.mainloop()
