#from socket import AF_INET, socket, SOCK_STREAM
import socket
import json
import datetime
from threading import Thread
from ConnectionHandler import *
from Log import *

class Client:
    BUFFER_SIZE = 2048
    PORT_SERVER = 6000
    PORT_P2P = 7000
    HOST_SERVER = '127.0.0.1'
    CODE_TYPE = 'utf-16'
    socketClient = {}
    JSON = False

    def __init__(self, hostServer, portServer):
        self.hostServer = self.HOST_SERVER #IPv4 Address of the server
        self.portServer = self.PORT_SERVER
        self.portp2p = random.randint(6001,60000)
        self.Log = Log()
        self.Log.log('Client initialized')
    #Functions to communicate with Server#
    '''
    Send a Message, containing the parameter text, to the Server
    encoded with utf-16
    If the communication with the server is closed return -1
    else return the return of the send function [a number > 0]
    '''
    def sendServer(self, text):
        ret = self.socketServer.send(text.encode(self.CODE_TYPE))
        if ret == 0:
            #Socket is close
            self.Log.log('Problem in the connection with the server')
            return -1
        else:
            self.Log.log('Message: <' + text + '> sended to the server correctly')
            return ret

    '''
        Open the connection with the server creating the socket [socketServer]
        if the connection goes wrong the function return -1 otherwise 1
    '''
    def connectServer(self) :
        try :
            self.socketServer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socketServer.connect((self.hostServer, self.portServer))
            return 1
        except :
            print('Connection refused by the server! Please try again later!')
            self.Log.log('Error in connection with the server, is it down?')
            return -1

    '''
        Used, after the Login is done correctly, to retrieve all the waiting
        messages in the server sended to me from other users while I was offline
        All the messages are taken and putted in a structure containing all the
        messages related to the specific connection with that specific user
        TO FINISH
    '''
    def retrieveMessage(self, msgs) :
        msg = msgs.split('^/')
        for x in msg :
            block = x.split('/^')
            print('sender :' + block[0])
            print('text : ' + block[1])
            print('time : ' + block[2])

    '''
        Receive Messages from the server
        if the socket is closed or there is an exception return -1
        otherwise it returns a specific value depending on the message received
        by the server
    '''
    def receiveServer(self):
        try:
            ret = self.socketServer.recv(self.BUFFER_SIZE)
            if not ret:
                self.Log.log('Connection with the server closed!')
                return -1
            else:
                msg = ret.decode(self.CODE_TYPE)
                self.Log.log('Received a message from the SERVER: ' + msg)
                msgs = msg.split('|')
                identifier = msgs[0]
                #The server can send a simple 0 if there are no messages pending
                if(len(msgs) > 1) :
                    value = msgs[1]
                #If it is a digit then the login is done correctly and we
                #are waiting to know if there are messages stored in the server
                if identifier.isdigit():
                    if int(identifier) > 0 :
                        self.Log.log('There are messages pending in the server')
                        self.retrieveMessage(msgs[1]);
                    else :
                        self.Log.log('No messages stored in the server')
                    return 1
                    #if ! we are waiting to know the IP of the host we want to connect to
                elif identifier == '!' :
                    return value
                    #if ? we are waiting to know if the login is gone
                elif identifier == '?' :
                    return value
                    #if - we are waiting to know how the registration is gone
                elif identifier == '-' :
                    return value
                    #if . we are waiting to know if a message sended to be stored
                    #in the server has been succesfully received and stored
                elif identifier == '.' :
                    return value
                else :
                    print('The protocol for this kind of message has not been implemented yet')
                    return identifier
        except:
            self.Log.log('An Exception has been raised in the receiveServer function')
            return -1
    ######################################

    #Functions for the FrontEnd#
    '''
        send a message to the server to register
        The message is sent with the prefix '1|'
        if succesfull registration return 1
        otherwise return 0 {we can use other codes to know why it is not okay}
    '''
    def register(self, username, password, name, surname, email, key):
        self.sendServer('1|' + username + ',' + password + ',' + name + ',' +
                surname + ',' + email + ',' + key)
        value = int(self.receiveServer());
        if value == 1 :
            self.Log.log('Succesfully registered')
        else :
            #we can handle better the possible error
            self.Log.log('Error in registration')
        return value
    '''
        Used to do the login -> creates an attribute to know the username [username]
        Send a message to the server with the prefix '2|'
        If all it's correct return 1
        if the username or password are wrong return 0
        if the host is already connected with another device return -1
    '''
    def login(self, username, password):
        self.username = username
        self.sendServer('2|' + username + ',' + password + ',' + str(self.portp2p))
        value = int(self.receiveServer())
        if value == 1 :
            self.Log.log('Succesfull logged in as ' + self.username)
            #restore saved messages
            #TO DO TO DO TO DO
            #wating to know if there are waiting messages on the server
            self.receiveServer()

            #starting the connectionHandler in order to manage
            #connections received from new clients
            ch = ConnectionHandler(self.portp2p, self.Log)
            ch.start()
        elif value == 0 :
            self.Log.log('Login : Wrong Username or Password')
        elif value == -1 :
            self.Log.log('Login : You are already connected with another device')
        else:
            self.Log.log('Login : an unreachable part of the code has been reached ' + value)
        return value
    '''
    Start a new connection with the user [receiver]:
        The message is sent with the prefix '3|'
        if it is online and all goes in the correct way then return 1
        -> creates the new socket with the receiver [socketClient[receiver]]
        else if receiver is offline return 0
             if you do not have done the login return -1
             if you are trying to talk to yourself return -2
             if the receiver does not exist -3
             if an exception has been raised -4
    '''
    def startConnection(self, receiver):
        self.sendServer('3|' + receiver)
        value = self.receiveServer()
        msg = ''

        if value == '0' :
            msg = 'user offline'
        elif value == '-1' :
            msg = 'Error: user does not have done the login'
        elif value == '-2' :
            msg = 'Error: you can not connect with yourself'
        elif value == '-3' :
            msg = 'Error: the contacted user does not exist'
        else :
            msgs = value.split(':')
            ip = msgs[0]
            port = msgs[1]
            msg = receiver + ' has IP:Port : ' + value
            self.Log.log('Starting a new connection with ' + receiver)
            try:
                self.socketClient[receiver] = socket.socket()
                self.socketClient[receiver].connect((ip, int(port)))
                username = self.username + '\^'
                ret = self.socketClient[receiver].send(username.encode(self.CODE_TYPE))
                value = 1
                if ret == 0:
                    msg = 'Error in sending the message to the client connection redirected to the server'
                    self.socketClient[receiver] = 'server'
            except:
                self.Log.log('An exception has been raised in the startConnection function')
                return -4
        self.Log.log(msg)
        return int(value)

    '''
        Used to send and store a message in the server for an offline user
        The message is sent with the prefix '4|'
        if the message has been sent correctly return 1
        if there was an error in the db and the message has not been saved return 0
        otherwise return -1 for general errors
    '''
    def sendMessageOffline(self, receiver, text, time):
        self.sendServer('4|' + receiver + '/^' + text + '/^' + time)
        value = int(self.receiveServer())
        if value == 1:
            self.Log.log('Message send correctly')
        elif value == 0:
            self.Log.log('Error in the database! Try again later!')
        return value

    '''
        Used to send a message [text] to the user [receiver]
        checks if there is an existing connection with the user [receiver]
        if not then it tries to create the p2p connection if not possible
        and the user exists then send the message to the server
        Handles the passage of the receiver from online to offline
    '''
    def sendClient(self, receiver, text):
        #Handle sending of messages
        if not receiver in self.socketClient.keys() :
            value = self.startConnection(receiver)
            if value == 0 : #client offline
                self.socketClient[receiver] = 'server'
            elif value == 1 : #client online, connection established correctly
                self.Log.log('Connection established with ' + receiver)
                #self.socketClient[receiver].send(text.encode(self.CODE_TYPE))
            else :
                print('Client does not exist!!!')
                return value
        if self.socketClient[receiver] == 'server' :
            #Check after x time if receiver is now online
            return self.sendMessageOffline(receiver, text, str(datetime.datetime.now()).split('.')[0])
        else :
            try:
                value = self.socketClient[receiver].send(text.encode(self.CODE_TYPE))
                if value > 0:
                    return 1
                else :
                    return 0
            except:
                self.Log.log(receiver + 'has disconnected')
                #possible signal to FrontEnd
                self.socketClient[receiver] = 'server'
                self.sendClient(receiver, text)

'''
        if msg == "{quit}":
            client_socket.close()
            top.quit()

    def onClosing(event=None): #clean up before close
        #close the socket connection
        my_msg.set("{quit}")
        send()

    #Functions for the Security#
    ##TO DO TO DO  TO DO TO DO##
    ############################
'''
