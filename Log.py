import threading
import datetime
class Log:
    def __init__(self):
        self.lock = threading.Lock()
        self.file = open("tempLog.txt","w")
    def log(self,_log):
        with self.lock:
            time = str(datetime.datetime.now()).split('.')[0]
            text = str(time) + "\t"+str(_log)+"\n"
            self.file.write(text)
            self.file.flush()
