from tkinter import *

class LoginGUI(Tk):

    backgroundWindow = '#47476b'
    def __init__(self):
        Tk.__init__(self)
        w = 300 # width for the Tk root
        h = 300 # height for the Tk root
        ws = self.winfo_screenwidth() # width of the screen
        hs = self.winfo_screenheight() # height of the screen

        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)

        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.resizable(width=FALSE, height=FALSE)
        self.title("Login")
        self.mainFrame = Frame(self, bg=self.backgroundWindow)

        self.titleLabel = Label(self.mainFrame, text="Login", bg=self.backgroundWindow, font = ("Default", 18, "bold"), fg='white')

        self.messageLabel = Label(self.mainFrame, bg="#8585ad")

        self.usernameLabel = Label(self.mainFrame, bg=self.backgroundWindow, fg='white', text="Username")
        self.usernameEntry = Entry(self.mainFrame )
        self.passwordLabel = Label(self.mainFrame, text="Password", bg=self.backgroundWindow, fg='white')
        self.passwordEntry = Entry(self.mainFrame, show="*")
        self.buttonsFrame = Frame(self.mainFrame, bg=self.backgroundWindow )
        self.signUpButton = Button(self.buttonsFrame, text="Sign Up", command=self.signUpEvent)
        self.confirmButton = Button(self.buttonsFrame, text="Confirm", command=self.loginEvent)

        self.mainFrame.pack(fill=BOTH, expand=True)
        self.mainFrame.columnconfigure(0, weight=100)
        self.titleLabel.grid( row=0, pady=15)
        self.usernameLabel.grid(row=2, pady=5)
        self.usernameEntry.grid(row=3, pady=5)
        self.passwordLabel.grid(row=4, pady=5)
        self.passwordEntry.grid(row=5, pady=5)
        self.buttonsFrame.grid(row=6, pady=10)
        self.signUpButton.pack(side="left", padx=5, pady=5)
        self.confirmButton.pack(side="right", padx=5, pady=5)

        self.bind('<Return>', self.pressEnterEvent)
        self.usernameEntry.focus_force()


    def setSignUpWindow(self, signUpWindow):
        self.signUpWindow = signUpWindow

    def setItems(self, client, chatWindow):
        self.client = client
        self.chatWindow = chatWindow

    def signUpEvent(self):
        self.withdraw()
        self.signUpWindow.deiconify()

    def loginEvent(self):
        if not self.usernameEntry.get() or not self.passwordEntry.get() :
            self.confirmButton.config(fg = "red", highlightbackground="red", highlightcolor="red", highlightthickness=1)
        else:
            ret = self.client.login(self.usernameEntry.get(),self.passwordEntry.get())
            if  ret == 1:
                self.withdraw()
                self.chatWindow.onLoginEvent()
            elif ret == 0:
                self.showError()
            elif ret == -1:
                self.showMessage("You are already logged in other device",  "#ff1a1a" )
            # self.client.login(self.usernameEntry.get(),self.passwordEntry.get())

    def pressEnterEvent(self, event):
        self.loginEvent()

    def showError(self):
        self.messageLabel.config(text="Username or Password is incorrect", fg = "#ff1a1a")
        self.messageLabel.grid(row = 1)
        self.usernameEntry.config(fg = "red", highlightbackground="red", highlightcolor="red", highlightthickness=1)
        self.passwordEntry.config(fg = "red", highlightbackground="red", highlightcolor="red", highlightthickness=1)

    def hideMessage(self):
        self.messageLabel.grid_forget()

    def showMessage(self, message, color):
        self.messageLabel.config(text=message, fg = color)
        self.messageLabel.grid(row = 1)


# login = LoginGUI()
#
# login.mainloop()
