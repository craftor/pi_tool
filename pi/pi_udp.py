from udp_cmder import udp_cmder
from udp_listener import udp_listener

import time
import threading

class broadcastThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.cmder = udp_cmder(1060)

    def run(self):
        while True:
            self.cmder.broadcast()
            time.sleep(5)

class receiverThread (threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.receiver = udp_listener(1060)

    def run(self):
        self.receiver.run()


t1 = broadcastThread()
t2 = receiverThread()

t1.start()
t2.start()