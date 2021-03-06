import socket
from threading import Thread
from Log import *
from User import User
from Security.Security import Security
import json
import os
import random

class ClientHandler(Thread):
    """
        Used to handle the new user whenever he try to connect to the server.
        This mechanism implies that for each user there is an appropriate thread that handle all the
        requests coming from that clinet
    """
    MSG_LEN = 10240
    def __init__(self,Conn,ip,port,db,clients,Log,XML):
        """
            Instatiate all the variabile and create the security module for the handled user

            :type Conn: Socket
            :param Conn: The socket used to send and receive data from and to the client
            :type ip: String
            :param ip: The ip address of the handled clients
            :type port: Int
            :param port: The port to communicate with the handled user
            :type db: Database
            :param db: The database module to store and find information in the database
            :type clinets: List<User>
            :param clients: The array of online client
            :type Log: Log
            :param Log: The module able to log the information on a FileNotFoundError
            :type XML: XMLHandler
            :param XML: The XML module able to obtain the parameter from thr XML File
        """
        Thread.__init__(self)   #Instatation of the thread
        self.HandledUser = User(Conn,ip,0,port,"none")
        self.DB = db
        self.OnlineClients = clients
        self.log = Log
        self.XML = XML
        self.HandledUser.addSecurityModule(Security(self.XML.getPemPath(),self.XML.getBackupPemPath()))
        self.logged = False
        self.log.log("Client handled has address: "+ self.HandledUser.getIp() +" and port "+str(self.HandledUser.getServerPort()))
        self.serverNonce = self.HandledUser.GetSecurityModule().generateNonce(11)

    def run(self):
        """ Waiting for the message coming from the associate client """
        while self._is_stopped == False:
            #Receiving the data from the handled client
            try:
                data = self.HandledUser.getSocket().recv(self.MSG_LEN)
            except ConnectionResetError:
                self.log.log("Client had a problem, connection closed")
                if self.HandledUser in self.OnlineClients.values():
                    del self.OnlineClients[self.HandledUser.getUserName()]
                return
            #Check if the connection is closed analyzing the data (0 means that is close)
            if not data:
                self.log.log("Client disconnected, closing this thread")
                if self.HandledUser in self.OnlineClients.values():
                    del self.OnlineClients[self.HandledUser.getUserName()]
                return
            if self.logged == False:
                try:
                    #Check if there is a Digest
                    msg,d = self.HandledUser.GetSecurityModule().splitMessage(data,32)
                    msg = self.HandledUser.GetSecurityModule().RSADecryptText(msg)
                except:
                    #Otherwise check if it was signed
                    msg,d = self.HandledUser.GetSecurityModule().splitMessage(data,256)
                    msg = self.HandledUser.GetSecurityModule().RSADecryptText(msg)
            else:
                msg= self.HandledUser.GetSecurityModule().AESDecryptText(data)
            if msg is None:
                self.log.log("Cannot decrypt the message")
            else:
                jsonMessage = json.loads(msg.decode('utf-8'))
                #Registration
                if jsonMessage['id'] == "1":
                    self.registerUser(jsonMessage,d)
                #Login
                elif jsonMessage['id'] == "2":
                    self.login(jsonMessage,msg,d)
                #Find the state and the address of another user
                elif jsonMessage['id'] == "3":
                    self.findUser(jsonMessage);
                #Store the message waiting for the user
                elif jsonMessage['id'] == "4":
                    self.StoreMessage(jsonMessage)
                #logout
                elif jsonMessage['id'] == "0":
                    del self.OnlineClients[self.HandledUser.getUserName()]
                    self.HandledUser.setUserName("none")
                    self.serverNonce = self.HandledUser.GetSecurityModule().generateNonce(11)
                    self.HandledUser.addSecurityModule(Security(self.XML.getPemPath(),self.XML.getBackupPemPath()))
                    self.logged = False

    def login(self,message,data,signature):
        """
            Login with inserted credential and search in the Database if the information
            sended are correct, in this case if there are several messagges sended to the user when
            he was offline, the server send them , specifying the sender and also the time (yy-mm-dd hh-mm-ss)

            :type message: Dictionary
            :param message: The dictionary created by the json message receveid
            :type data: Bytes
            :param data: The raw data reppresenting the message as Received
            :type signature: Bytes
            :param signature: The signature of data
        """
        self.log.log("A client want to login")

        key = self.DB.getSecurityInfoFromUser(message['username'])
        if key is None:
            self.log.log("The user is not present")
            response['id'] = "?"
            response['status'] = "0"
            jsonResponse = json.dumps(response)
            self.log.log("Login Failed")
            self.HandledUser.getSocket().send(jsonResponse.encode('utf-8'))
            return

        self.HandledUser.GetSecurityModule().AddClientKey(key[0].encode('utf-8'))
        #Check if the signature is valid
        if(self.HandledUser.GetSecurityModule().VerifySignature(data,signature) == False):
            self.log.log("Signature Invalid, aborting login procedure")
            return

        response = {}
        #Check if this user is already Logged In
        if self.HandledUser in self.OnlineClients.values():
            response['id'] = "?"
            response['status'] = "-1"
            jsonResponse = json.dumps(response)
            signature = self.HandledUser.GetSecurityModule().getSignature(jsonResponse.encode('utf-8'))
            ct = self.HandledUser.GetSecurityModule().RSAEncryptText(jsonResponse.encode('utf-8'))
            self.HandledUser.getSocket().send(ct+signature)
            self.log.log("The request is sended by an user already logged in")
        elif self.DB.CredentialCorrect(message['username'].lower(),message['password']):
            response['id'] = "?"
            response['status'] = "1"
            #Generating the symmetric key used in communication with this client from now on
            self.HandledUser.GetSecurityModule().generateSymmetricKey(128,self.serverNonce)
            #Adding the nonce used to encapsulate some information for the clients key exchange
            self.HandledUser.GetSecurityModule().AddPacketNonce(message['clientNonce'])
            response['clientNonce'] = message['clientNonce']
            response['serverNonce'] = self.serverNonce
            #Getting the symmetric key as a dict in order to serialized in a json
            response['key'] = int.from_bytes(self.HandledUser.GetSecurityModule().getSymmetricKey(),byteorder='big')
            #Preparing the internal structure used to handle te connection between different clinet
            self.HandledUser.setUserName(message['username'].lower())
            self.HandledUser.setClientPort(message['porta'])
            key,g,p = self.DB.getSecurityInfoFromUser(self.HandledUser.getUserName())
            if key is not None:
                self.HandledUser.GetSecurityModule().AddClientKey(key.encode('utf-8'))
                self.HandledUser.GetSecurityModule().addDHparameters(p,g)
            else:
                self.log.log("Error in retriving security informations")
            jsonResponse = json.dumps(response)
            signature = self.HandledUser.GetSecurityModule().getSignature(jsonResponse.encode('utf-8'))
            ct = self.HandledUser.GetSecurityModule().RSAEncryptText(jsonResponse.encode('utf-8'))
            #Informing the client about the correctness of the login procedure
            self.HandledUser.getSocket().send(ct+signature)
            #Adding the client to the list of active users
            self.OnlineClients[message['username'].lower()] = self.HandledUser
            self.logged = True
            ct = self.HandledUser.getSocket().recv(2048)
            pt = self.HandledUser.GetSecurityModule().AESDecryptText(ct)
            if pt is None:
                self.log.log("Error in decrypt with AESCGM")
                return
            else:
                response = json.loads(pt.decode('utf-8'))
                if response['serverNonce'] == self.serverNonce:
                    msg = self.DB.getMessageByReceiver(self.HandledUser.getUserName())
                    response = {}
                    if len(msg.keys()) == 0:
                        self.log.log("There are no message for this client")
                        response['id'] = "0"
                        jsonResponse = json.dumps(response)
                        #Informing the user that there are no message for him
                    else:
                        lens = len(msg)
                        self.log.log("There are "+str(lens)+" message for "+self.HandledUser.getUserName())
                        response['id'] = str(lens)
                        response['messages'] = {}
                        response['messages'] = msg
                        jsonResponse = json.dumps(response)
                        #Removing the messagess previously obtained
                        self.DB.remove_waiting_messages_by_receiver(self.HandledUser.getUserName())
                    ct = self.HandledUser.GetSecurityModule().AESEncryptText(jsonResponse.encode('utf-8'))
                    if ct is None :
                        self.log.log("Error in encrypt with AESCGM")
                    else:
                        self.HandledUser.getSocket().send(ct)
                        self.HandledUser.nonce = self.serverNonce
                        self.log.log("Login completed correctly")
                else:
                    self.log.log("Connection is not fresh removing user")
                    del self.OnlineClients[self.HandledUser.getUserName()]


        else:
            response['id'] = "?"
            response['status'] = "0"
            jsonResponse = json.dumps(response)
            self.log.log("Login Failed")
            # QUESTO NON VA CIFRATO
            self.HandledUser.getSocket().send(jsonResponse.encode('utf-8'))

    def registerUser(self,message,digest):
        """ Insert the information of the user in the database, checking if there is another user with the same Username
            and sending back the result

            :type message: Dictionary
            :param message: The dictionary created by the received json message
            :type digest: Bytes
            :param digest: The digest created by the data corresponding to the message creator of the dictionary
        """
        checkdigest = self.HandledUser.GetSecurityModule().generateDigest(json.dumps(message).encode('utf-8'))
        if digest != checkdigest:
            self.log.log("Error in the hash,aborting the registration procedure")
            #This recv is present because the client doesn't know if the signature is valid
            self.HandledUser.getSocket().recv(2048)
            return

        self.log.log("A client want to register")
        self.log.log("Wait for the public key")
        #Waiting for the public key
        msg = self.HandledUser.getSocket().recv(4096)
        hash = msg[-32:]
        publicKey = msg[:-32]
        digest =  self.HandledUser.GetSecurityModule().generateDigest(publicKey+message['clientNonce'].to_bytes(6, byteorder='big'))
        if digest != hash:
            self.log.log("Error in the hash of the key,aborting the registration procedure")
            return

        if not publicKey:
            self.log.log("Problem during the receiving of the public key, aborting the registration procedure")
            return

        self.HandledUser.GetSecurityModule().AddClientKey(publicKey)
        response = {}
        if (self.DB.insert_user(message['user'].lower(),message['password'],message['name'].lower(),message['surname'].lower(),message['email'].lower(),publicKey.decode()) == 0):
            #Send to the client that the request has succeded
            response['id'] = "-"
            response['status'] = "1"
        else:
            self.log.log("Registration failed")
            #Send to the client that the request has failed
            response['id'] = "-"
            response['status'] = "0"
            jsonResponse = json.dumps(response)
            signature = self.HandledUser.GetSecurityModule().getSignature(jsonResponse.encode('utf-8'))
            ct = self.HandledUser.GetSecurityModule().RSAEncryptText(jsonResponse.encode('utf-8'))
            self.HandledUser.getSocket().send(ct+signature)
            return

        #Preparing the nonce according the protocol
        response['clientNonce'] = message['clientNonce']
        response['serverNonce'] = self.serverNonce
        jsonMessage = json.dumps(response)
        signature = self.HandledUser.GetSecurityModule().getSignature(jsonMessage.encode('utf-8'))
        ct = self.HandledUser.GetSecurityModule().RSAEncryptText(jsonMessage.encode('utf-8'))
        self.HandledUser.getSocket().send(ct+signature)

        #If the registration has succeded the server wait for the DH parameters generated by client
        if response['status'] == "1":
            self.log.log("Wait for the DH parameters")
            #Wait for the parameter
            ReceivedCt = self.HandledUser.getSocket().recv(self.MSG_LEN)
            #Verifying that the paramter are correctly received
            if not ReceivedCt:
                self.log.log("Error in receiving the dh parameters, removing the user")
                self.Database.remove_user(message['user'])
                return
            ct,d  = self.HandledUser.GetSecurityModule().splitMessage(ReceivedCt,256)
            pt = self.HandledUser.GetSecurityModule().RSADecryptText(ct)
            # check if the signature is correct
            if self.HandledUser.GetSecurityModule().VerifySignature(pt,d) == True:
                jsonResponse = json.loads(pt.decode('utf-8'))
                #Check if it is the actual session
                if jsonResponse['serverNonce'] == response['serverNonce'] :
                    #inserting the DH parameter in the DB
                    if self.DB.insertDHParameter(message['user'],jsonResponse['p'],jsonResponse['g']) == 0:
                        self.log.log("DH parameters inserted correctly")
                        d = self.HandledUser.GetSecurityModule().generateDigest(pt)
                        ct = self.HandledUser.GetSecurityModule().RSAEncryptText(d)
                        signature = self.HandledUser.GetSecurityModule().getSignature(d)
                        self.HandledUser.getSocket().send(ct+signature)
                        self.log.log("Registration completed correctly")
                    else:
                        self.log.log("Error in the insertion of the DH parameters,removing the user")
                        self.DB.remove_user(message['user'])
                        return
                else:
                    self.log.log("Session incorrect, removing user")
                    self.DB.remove_user(message['user'])
                    return
            else:
                self.log.log("Signature incorrect, removing the user")
                self.DB.remove_user(message['user'])
                return

    def StoreMessage(self,message):
        """ Store the message in the database waiting that the client come back online

            :type message: Dictionary
            :param message: The dictionary created by the received json message
        """
        sender = self.HandledUser.getUserName()
        self.log.log("Storing a message coming from "+sender)
        response = {}
        if self.DB.insert_message(sender,message['Receiver'],str(message['Text']),message['Time']) == 0:
            response['id'] = "."
            response['status'] = "1"
        else:
            response['id'] = "."
            response['status'] = "0"
        jsonResponse = json.dumps(response)
        ct = self.HandledUser.GetSecurityModule().AESEncryptText(jsonResponse.encode('utf-8'))
        self.HandledUser.getSocket().send(ct)
        self.log.log("Message stored correctly")

    def findUser(self,message):
        """
            Find the information about the user (IPaddress:clientPort) related to the username passed as parameter

            :type message: Dictionary
            :param message: The dictionary created by the json message received
        """
        self.log.log("A client want to find another user")
        response = {}
        if self.HandledUser not in self.OnlineClients.values():
            self.log.log("Cannot found the associate user")
            response['id'] = "!"
            response['status'] = "-1"
        else:
            if message['username'].lower() in self.OnlineClients.keys():
                #Check if the client asks for its own import ip
                if self.OnlineClients[message['username'].lower()] == self.HandledUser:
                    self.log.log("The user want to talk with himself")
                    response['id'] = "!"
                    response['status'] = "-2"
                 #Otherwise the server provide the ip of the client and the clientPort and the Security parameter
                else:
                    FoundUser = self.OnlineClients[message['username'].lower()]
                    response['id'] = "!"
                    response['status'] = FoundUser.getIp()+":"+str(FoundUser.getClientPort())
                    response['key'] = FoundUser.GetSecurityModule().getSerializedClientPublicKey().decode('utf-8')
                    response['p'],response['g'] = FoundUser.GetSecurityModule().getDHparameters()
                    #Preparing the packet with the information about the starter of the conversation
                    info = {}
                    info['key'] = self.HandledUser.GetSecurityModule().getSerializedClientPublicKey().decode('utf-8')
                    info['Nsa'] = self.HandledUser.GetSecurityModule().nonce
                    info['Nsb'] = FoundUser.GetSecurityModule().nonce
                    info['username'] = self.HandledUser.getUserName()
                    pt = json.dumps(info).encode('utf-8')
                    ct = FoundUser.GetSecurityModule().PacketAESEncryptText(pt)
                    if ct is None:
                        self.log.log("Error in encrpt the packet ")
                        response['lenInfo'] = 0
                        response['info'] = 0
                    else:
                        response['lenInfo'] = len(ct)
                        response['info'] = int.from_bytes(ct,byteorder='big')
                    self.log.log("Ip found: "+response['status'])
            else:
                #Check if the receiver is not registered
                if self.DB.userIsRegistered(message['username'].lower()) == 0:
                    response['id'] = "!"
                    response['status'] = "-3"
                    self.log.log(message['username']+" is not registered")
                else:
                    self.log.log("The user "+message['username'].lower()+" is offline")
                    response['id'] = "!"
                    response['status'] = "0"
                    SecurityParameters = self.DB.getSecurityInfoFromUser(message['username'].lower())
                    response['key'] = SecurityParameters[0]
        jsonResponse = json.dumps(response)
        #Using symmetric key criptography because this request can be done only by logged user
        ct = self.HandledUser.GetSecurityModule().AESEncryptText(jsonResponse.encode('utf-8'))
        if ct is None:
            self.log.log("Error in encrptying with AES")
            return
        self.HandledUser.getSocket().send(ct)

    def getHandledUser(self):
        """
            This function gets back the username associate to the handled client

            :rtype: String
            :return: The name of the user handled by this thread
        """
        return self.HandledUser.getUserName()
