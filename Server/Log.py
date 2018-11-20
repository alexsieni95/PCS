import threading
import datetime
class Log:
    def __init__(self,enableLog,path):
        """ Open the file in write mode (overwriting the precedent content) and instatiate a lock
            Parameter:
                    enableLog   : Boolean variable meaning if the log must be enable or not : Boolean
                    path        : The path of the log file                                  : string
            Return :
                    Void - Constructor """
        self.lock = threading.Lock()
        self.file = open(path,"w")
        self.enableLog = enableLog


    def log(self,_log):
        """ Save in the opened file the string passed as argument with a timestamp prefixed, in order to define when
            the action logged is happened
            Parameter:
                    _log : The string that must be saved in the file    : string
            Return:
                    Void    """
        with self.lock:
            if self.enableLog:
                #Obtaining the timestamp of this moment
                time = str(datetime.datetime.now()).split('.')[0]
                #Preparing the log statement
                text = str(time) + "\t"+str(_log)+"\n"
                #Writing the log in the file
                self.file.write(text)
                # Flushing the stream in order to log the events in real time
                self.file.flush()


    def closeFile(self):
        """ Close the file
            Parameter:
                    Void
            Return:
                    Void   """
        self.file.close()
