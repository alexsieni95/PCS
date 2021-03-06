import pymysql

class Database:

    #In the init function the class try to establish a connection with the database, in order to allows
    #the programmer to modify the information stored in the database using the methods offered by this class

    def __init__(self,_host,_port,_user,_password,_db):
        """
            Establish the connect with the databaes and instatiate the cursor useful to execute the queries
            :type _host : String
            :param _host: The IP address of the database
            :type _port: Int
            :param _port: The port in which the database is listening
            :type _user: String
            :param _user: The username to login to the database
            :type _password: String
            :param _password: The password to login to the database
            :type _db: String
            :param _db: The name of the database
        """

        #Establishing the connection with the database
        self.db = pymysql.connect(host=_host, port=_port, user=_user, passwd=_password, db=_db)
        #Creating a cursor useful to execute the desired query
        self.cursor = self.db.cursor()


    def insert_user(self,user,password,name,surname,email,key):
        """
            Insert a new user a is invoked when a new user has completed the registration form on the client application,

            :type user: String
            :param user: username
            :type password: String
            :param password: password
            :type name: String
            :param name: Name of the user
            :type surname: String
            :param surname: surname of the user
            :type email: String
            :param email: Email of the user
            :type key: String
            :param key: The public ket generated by the user

            :rtype: Int
            :return: 0 if all is done correctly\n
                     -1 if an error happened
        """

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
        """
            Insert the message in the database with all its own information,

            :type sender: String
            :param sender: The username of the sender
            :type receiver: String
            :param receiver: The username of the receiver
            :type message: String
            :param message: The text of the message
            :type time: String
            :param time: The time in which the message is sended (dd-mm-yyyy)

            :rtype: Int
            :return: 0 if all is done correctly\n
                     -1 if an error happened
        """

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
        """
            Insert the Diffie Helmann parameter after of the registered user

            :type user: String
            :param user: the username associated with the parameter
            :type p: Int
            :param p: the P parameter
            :type g: Int
            :param g: the G parameter

            :rtype: Int
            :return: 0 if the insertion is done correctly\n
                     -1 if an error happened
        """

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
            return -1

    def getMessageByReceiver(self,receiver):
        """
            Obatain all the message waiting for that user

            :type receiver: String
            :param receiver: The username of the receiver

            :rtype: Dictionary
            :return: An array of dictionary containing all the information about the messages \n
                     ['Sender'] means The sender of the message as String\n
                     ['Text'] means The text of the message as String\n
                     ['Time'] means The time in which the message is sended as String
        """

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
            return request
        except Exception as e:
            #rollback to the previous operations
            self.db.rollback()
            print (e)
            return -1

    def getSecurityInfoFromUser(self,_user):
        """
            Obtain the security parameter of an user as a list

            :type _user: String
            :param _user: The username of the user of which we want the security information

            :rtype: [String,Int,Int] or None
            :return: The list of security information "Public key and DH parameters as [PublicKey,G,P] or None if
                     an error happened during the search of the information
        """

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
        """
            Control if the credential passed as arguments are corrected,

            :type _user: String
            :param _user: the username used to login
            :type _password: String
            :param _password: the password used to login

            :rtype: Int
            :return: 0 if The combination user/password is incorrect\n
                     1 if he combination user/password is correct\n
                     -1 if An error happened
            """

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
        """
            Check if the user is registred,

            :type _user: String
            :param _user: The username to check
            :rtype: Int
            :return: 0 if the username is not present in the database\n
                     1 if the username is present in the database\n
                     -1 if An error happened
        """

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
        """
            Remove that user from the database
            :type user: String
            :param user: The username of the user to remove

            :rtype: Int
            :return: 0 if the operation is done correctly\n
                     -1 if an error happened\n
        """

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
        """
            Remove all the message destined to the user passed as argument from the database
            :type receiver: String
            :param receiver: The username of the user we want to delete all the messages

            :rtype: Int
            :return: 0 if the operation is done correctly\n
                     -1 if an error happened\n
        """

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
    #At the end of the execetion the server close the connection with the database invoking this method

    def close_connection(self):
        """
            Close the connection with the database
        """
        self.db.close()
