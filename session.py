__author__ = 'RAEON'

import websocket
import threading
import struct

class Session(object):

    def __init__(self):
        self.running = False

        self.thread = None
        self.ws = None

        self.host = ''
        self.port = 443

        self.inbound = []

    def connect(self, host, port):
        self.host = host
        self.port = port
        if not self.is_connected():
            if type(port) == int:
                port = str(port)

            url = 'ws://' + host + ':' + port + '/'
            try:
                self.ws = websocket.WebSocket()
                self.ws.connect(url, origin='http://agar.io')

                # if we got here, we connected!
                self.running = True

                self.inbound = []

                self.thread = threading.Thread(name='SessionThread', target=self.run)
                self.thread.start()
                return True
            except Exception as ex:
                print('[session] Failed to connect to ' + url)
                # raise ex
        return False

    def disconnect(self):
        if self.is_connected():
            self.running = False
            self.thread = None
            try:
                if self.ws.connected:
                    self.ws.close()
            except:
                pass
            return True
        return False

    def is_connected(self):
        return self.running and self.ws.connected

    def run(self):
        while self.is_connected() and self.thread == threading.current_thread():
            try:
                if self.ws.connected:
                    data = self.ws.recv()
                    self.inbound.append(data)
            except Exception as ex:
                print("disconnecting...")
                self.ws.close()
                self.inbound = []
                print("disconnected, please wait for reconnection")

    def read(self):
        if self.is_connected():
            if len(self.inbound) > 0:
                data = self.inbound[0]
                self.inbound = self.inbound[1:]
                return data
        return None

    def write(self, data):
        if self.is_connected():
            # if type(data) == bytearray:
            #     data = bytes(data)  # no reason to do this

            print("TITS",data)

            if len(data) > 0:
                try:
                    self.ws.send(data)
                    return True
                except Exception as ex:
                    print('[session] write: ' + str(ex))
        return False

if __name__ == '__main__':
    ses = Session()
    ses.connect('45.33.102.76', 443)
