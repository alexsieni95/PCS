from tkinter import *
from PIL import ImageTk, Image
import datetime
from ScrollableFrame import *

class ChatWindow(Frame):
    backgroundWindow = '#1f2327'
    MAXMESSAGELEN = 200
    def __init__(self, master, background):
        """
            Right frame of the chatGUI, it contains the chat name, that display
            the receiver's status ( Online/Offline ), the list of messages and
            input bar

            :type master: ChatGUI
            :param master: parent widget

            :type background: string
            :param background: background color

        """
        Frame.__init__(self, master, background=self.backgroundWindow)

        self.chatName = StringVar()
        self.userState = StringVar()
        self.listBoxMessage = []
        self.rowconfigure(1, weight=8)
        Grid.columnconfigure(master, 1, weight=1)
        Grid.columnconfigure(master, 2, weight=4)
    def createWidgets(self, background, chatName, client, chatList ):
        """
            :type background: string
            :param background: background color

            :type chatName: string
            :param chatName: name of the chat

            :type client: Client
            :param client: instance of class Client

            :type chatList: ChatList
            :param chatList: list of available chats
        """
        self.chatName.set(chatName)
        self.client = client
        self.chatList = chatList

        inputBar = Frame(self, background=background,  padx=10, pady=10, highlightbackground="black", highlightcolor="black", highlightthickness=1)

        chatBar = Frame(self, bg = background, highlightbackground="black", highlightcolor="black", highlightthickness=1)
        chatNameLabel = Label(chatBar, textvariable=self.chatName, font = ( "Default", 10, "bold"), bg = background, fg='white')
        userStateLabel = Label(chatBar, textvariable=self.userState, font = ( "Default", 8, "italic"), bg = background, fg='white')
        mainFrame = Frame(self)
        self.scrollableFrame = Scrollable(mainFrame, self['bg'])

        chatBar.pack( side="top", fill=X, ipadx=5, ipady=4)
        chatNameLabel.grid(row=0, sticky=W, padx=10, pady=5)
        userStateLabel.grid(row=1, sticky=W, padx=10, pady=5)

        mainFrame.pack(fill=BOTH, expand=True)

        inputBar.pack(side="bottom", fill=X, ipadx=5, ipady=4)
        inputBar.columnconfigure(0, weight=15)
        inputBar.columnconfigure(1, weight=1)

        self.entryBar = Entry(inputBar, background=background, bd =0, fg='white')
        self.entryBar.grid(row=0, column=0, sticky=W+E)
        self.entryBar.bind('<Return>', self.pressEnterEvent )
        self.entryBar.bind('<Escape>', self.pressEscEvent)
        self.icon = ImageTk.PhotoImage(Image.open("Images/sendIcon.png").resize( (30,30), Image.ANTIALIAS ))
        sendButton = Button(inputBar, text="send", command=self.pressSendButton, bg=background, bd=0, activebackground='#787878', image=self.icon)
        sendButton.grid(row=0, column=1)
    def setClient(self, client):
        """
            :type client: Client
            :param client: instance of class Client
        """
        self.client = client
    def addBoxMessageElement(self, message, time, isMine):
        """
            Append a new message and diplay it into the frame on the right if
            it is a message sent by me or on the left if it is a received message

            :type message: string
            :param message: sent or received message

            :type time: string
            :param time: arrival or sending time

            :type isMine: boolean
            :param isMine: true if this is a message sent by me
        """
        timeString = str(time).split('.')[0].split(' ')[1][:-3]
        boxMessage = BoxMessage(self.scrollableFrame, self['bg'])
        boxMessage.createWidgets( message, timeString , isMine)
        boxMessage.bindMouseWheel(self.scrollableFrame)
        self.listBoxMessage.append(boxMessage)
        self.chatList.updateMessageTime(self.chatName.get(), message, time)
        self.scrollableFrame.update()
        self.scrollableFrame.canvas.yview_moveto( 1 )
    def getChatName(self):
        return self.chatName.get()
    def pressSendButton(self):
        """
            When send button is pressed the message is splitted into chunks in
            order to avoid length of packet problems. In this way, a very long
            message is splitted into n chunks and the client.sendClient is called
            n times, as they were n independent messages, so this is transparent
            to the receiver
        """
        message = str(self.entryBar.get())
        if not message:
            return
        chunks = [message[i:i+self.MAXMESSAGELEN] for i in range(0, len(message), self.MAXMESSAGELEN)]
        for c in chunks:
            self.send(c)
        self.entryBar.delete(0, 'end')
    def pressEnterEvent(self, event):
        """
            :type event: Event
            :param event: information about the event
        """
        self.pressSendButton()
    def send(self, message):
        """
            :type message: string
            :param message: message to be sent
        """
        self.addBoxMessageElement(message, datetime.datetime.now(), True)
        #the False is used for the non-logout messages
        status = self.client.sendClient(str(self.chatName.get().lower()), message, False)
        self.chatList.sortChatList(self.chatName.get().lower())
        self.updateState(status)
    def pressEscEvent(self, event):
        """
            :type event: Event
            :param event: information about the event
        """
        self.chatList.searchBar.focus_force()
        self.chatList.chatListDict[self.chatName.get().lower()][0].changeChatWindow(event=None)
    def updateState(self, status):
        """
            :type status: int
            :param status: online or offline
        """
        if status == 1:
            self.userState.set('Online')
        else:
            self.userState.set('Offline')

class BoxMessage(Frame):
    def __init__(self, master, background):
        """
            Frame containg the message and the arrival/sending time

            :type master: Scrollable
            :param master: parent widget

            :type background: string
            :param background: background color
        """
        Frame.__init__(self, master, padx=3, pady=3, bg=background )
        self.message = StringVar()
        self.time = StringVar()
        self.isMine = True
        self.pack(fill='x')
    def createWidgets(self, message, time, isMine):
        """
            :type message: string
            :param message: sent or received message

            :type time: string
            :param time: arrival or sending time

            :type isMine: boolean
            :param isMine: true if this is a message sent by me
        """
        rowFrame = Frame(self)
        self.messageLabel = Message(rowFrame, aspect=250, textvariable=self.message, padx=5, pady=2, fg='white')
        self.timeLabel = Label(rowFrame, textvariable=self.time, padx=5, pady=2, fg='white')

        self.message.set(message)
        self.time.set(time)
        self.isMine = isMine

        self.messageLabel.grid(row=0, column=0, sticky=N+S+W)
        self.timeLabel.grid(row=0, column=1, sticky=NE)

        backgroundMine = '#2a8c8c'
        backgroundIts = '#282e33'
        if isMine:
            rowFrame.pack(side='right', fill='x', padx=10, pady=5)
            rowFrame.configure(background=backgroundMine)
            self.messageLabel.configure(background=backgroundMine)
            self.timeLabel.configure(background=backgroundMine)
        else:
            rowFrame.pack(side='left', fill='x', padx=10, pady=5)
            rowFrame.configure(background=backgroundIts)
            self.messageLabel.configure(background=backgroundIts)
            self.timeLabel.configure(background=backgroundIts)
    def bindMouseWheel(self, scrollableFrame):
        """
            Bind mouse wheel event so the scrollableFrame can scroll even if the
            cursor is over this frame

            :type scrollableFrame: Scrollable
            :param scrollableFrame: instance of class Scrollable
        """
        self.bind('<MouseWheel>', scrollableFrame._on_mousewheel)
        self.messageLabel.bind('<MouseWheel>', scrollableFrame._on_mousewheel)
        self.timeLabel.bind('<MouseWheel>', scrollableFrame._on_mousewheel)
