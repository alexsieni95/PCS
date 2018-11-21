import pymysql

"""
This example module shows various types of documentation available for use
with pydoc.  To generate HTML documentation for this module issue the
command:

    pydoc -w foo

"""
class Database:

    """This class is able to manage the connection with the database"""

    #In the init function the class try to establish a connection with the database, in order to allows
    #the programmer to modify the information stored in the database using the methods offered by this class

    def __init__(self,_host,_port,_user,_password,_db):
        """ Establish the connect with the databaes and instatiate the cursor useful to execute the queries
            Parameters:
                    _host       : The IP address of the database                    : string
                    _port       : The port in which the database is listening       : int
                    _user       : The username to login to the database             : string
                    _password   : The password to login to the database             : string
                    _db         : The name of the database                          : string  """

        #Establishing the connection with the database
        self.db = pymysql.connect(host=_host, port=_port, user=_user, passwd=_password, db=_db)
        #Creating a cursor useful to execute the desired query
        self.cursor = self.db.cursor()


    def insert_user(self,user,password,name,surname,email,key):
        """ Insert a new user a is invoked when a new user has completed the registration form on the client application,
            Parameter:
                    user        : username                  : string
                    password    : password                  : string
                    name        : name of the user          : string
                    surname     : surname of the user       : string
                    email       : email of the user         : string
                    key         : key                       : string
            Returns:
                     0 : The insertion is done correctly    : int
                    -1 : An error happened                  : int  """

        #Preparing the insertion query
        query = "INSERT INTO user (UserName,Email,Name,Surname,Password,PublicKey) VALUES (%s,%s,%s,%s,%s,%s) "
        try:
            #Executing the query
            self.cursor.execute(query,(user,email,name,surname,password,str(key)))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print(e)
            return -1

    #This method is used to store a message in the database and is invoked when the receiver of that message is offline,
    #in order to send it when the last one will back online


    def insert_message(self,sender,receiver,message,time):
        """ Insert the message in the database with all its own information,
            Parameters:
                    sender      : The username of the sender                            : string
                    receiver    : The username of the receiver                          : string
                    message     : The text of the message                               : string
                    time        : the time in which the message is sended (dd-mm-yyyy)  : string
            Return:
                     0   : The insertion is done correctly                              : int
                    -1   : An error happened                                            : int """

        #Preparing the insertion query
        query = "INSERT INTO message(Sender,Receiver,Text,Time) VALUES (%s,%s,%s,%s)"
        try:
            #Executing the query
            self.cursor.execute(query,(sender,receiver,message,time))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1

    def insertDHParameter(self,user,p,g):
        """ Insert the Diffie Helmann parameter after of the registered user
            Parameters:
                    user    : the username associated with the parameter    : string
                    p       : the P parameter                               : int
                    g       : the G parameter                               : int
            Return:
                     0      : the insertion is done correctly               : int
                    -1      : an error happened                             : int  """

        query = "UPDATE user SET P = %s,G = %s WHERE userName = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(str(p),str(g),user))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback to the previous operations
            print(e)
            self.db.rollback()
            #print ("Error in the DH parameter insertion query")
            return -1

    def getMessageByReceiver(self,receiver):
        """ Obatain all the message waiting for that user as a dictionary with keys = 'Sender', 'Text' and 'Time'
            Parameter:
                    receiver: the username of the receiver                      : string
            Return :
                    request     : An array of dictionary containing all the information about the messages:
                        ['Sender']  : The sender of the message                 : string
                        ['Text']    : The text of the message                   : string
                        ['Time']    : The time in which the message is sended   : string
                    -1          : An error happened                             : int     """

        query = "SELECT Sender,Text,Time FROM message WHERE Receiver = %s"
        msg = []
        try:
            #Executing the query
            self.cursor.execute(query,(receiver))
            rows = self.cursor.fetchall()
            request = {}
            for i in range(0,len(rows)):
                request[i] = {}
                request[i]['Sender'] = rows[i][0]
                request[i]['Text'] = rows[i][1]
                request[i]['Time'] = str(rows[i][2])
            #print(request)
            return request
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1

    def getSecurityInfoFromUser(self,_user):
        """ Obtain the security parameter of an user as a list
            Parameter:
                    _user           : the username of the user of which we want the security information        : string
            Return:
                    [PublicKey,G,P] : the list of security information "Public key and DH parameters            : [string,int,int]
                    None:           : An error happened during the search of the information"""

        query = "SELECT PublicKey,G,P from user where UserName = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(_user))
            rows = self.cursor.fetchall()
            return [rows[0][0],rows[0][1],rows[0][2]]
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return None


    def CredentialCorrect(self,_user,_password):
        """ Control if the credential passed as arguments are corrected,
            Parameters:
                    _user       : the username used to login                    : string
                    _password   : the password used to login                    : string
            Return:
                     0          : The combination user/password is incorrect    : int
                     1          : The combination user/password is correct      : int
                    -1          : An error happened                             : int"""

        query = "SELECT * from user where UserName = %s AND Password = %s "
        try:
            #Executing the query
            self.cursor.execute(query,(_user,_password))
            #Obtaining the result as a list
            results = self.cursor.fetchall()
            return len(results) == 1
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1

    def userIsRegistered(self,_user):
        """ Check if the user is registred,
            Parameter:
                    _user   : the username to check                         : string
            Return:
                     0      : The username is not present in the database   : int
                     1      : The username is present in the database       : int
                    -1      : An error happened                             : int """

        query = "SELECT * from user where UserName = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(_user))
            #Obtaining the result as a list
            results = self.cursor.fetchall()
            return len(results) == 1
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1

    #If a user want to unscribe to our platform he can do it and this method is used to remove all his information from
    #the database

    def remove_user(self,user):
        """ Remove that user from the database
            Parameter:
                    user    : The username of the user to remove    : string
            Return:
                     0      : The operation is done correctly       : int
                    -1      : An error happened                     : int    """

        query = "DELETE from user WHERE UserName = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(user))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback the previous operations
            self.db.rollback()
            print (e)
            return -1

    #This method is invkoed when a user back online and there are several waiting message with him as receiver.

    def remove_waiting_messages_by_receiver(self,receiver):
        """ Remove all the message destined to the user passed as argument from the database
            Parameter:
                    receiver : the username of the user we want to delete all the messages  : string
            Return:
                     0       : The operation is done correctly                              : int
                    -1       : An error happened                                            : int   """

        query = "DELETE from message WHERE Receiver = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(receiver))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback the previous operations
            self.db.rollback()
            print (e)
            return -1
    '''
    def remove_waiting_messages_by_sender(self,sender):
        #DA RIMUOVERE


        query = "DELETE from message WHERE Sender = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(sender))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1

    def remove_waiting_messages_by_id(self,index):
        #DA RIMUOVERE



        query = "DELETE from message WHERE Index = %s"
        try:
            #Executing the query
            self.cursor.execute(query,(index))
            #Commit the changes to the databes
            self.db.commit()
            return 0
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1
    '''
    #At the end of the execetion the server close the connection with the database invoking this method

    def close_connection(self):
        """ Close the connection with the database
            Parameter:
                    void
            Return:
                    void """
        self.db.close()
