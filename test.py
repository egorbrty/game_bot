import time
import threading


def loop_poop():
    while True:
        print(time.ctime())
        time.sleep(1)

def loop_poop2():
    while True:
        print('азаза')
        time.sleep(1)


thread = threading.Thread(target=loop_poop)
thread.start()

thread2 = threading.Thread(target=loop_poop2)
thread2.start()