from client import Client
from PIL import ImageTk, Image
from Chat import ChatGUI
from Login import LoginGUI
from SignUp import SignUpGUI
import os

host = '127.0.0.1'
port = 6000
MESSAGE = 'hi'


if os.getcwd().find("Client") == -1:
    os.chdir("Client")


chat = ChatGUI()
login = LoginGUI()
signUp = SignUpGUI()
client = Client(host, port)
client.connectServer()

login.setSignUpWindow(signUp)
login.setItems(client, chat)
signUp.setLoginWindow(login)
signUp.setClient(client)
chat.createWidgets(client)


chat.withdraw()
signUp.withdraw()


chat.mainloop()
