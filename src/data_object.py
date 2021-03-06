import pickle
from constants import *  # -

import socket
 
# -
class DataObject:
    def __init__(self, s, host, port, list_id=None):  # -
        self.host = host  # address of server hosting lists        #-
        self.port = port  # the port it will be listening to       #-
        self.list_id = list_id  # the list for which this stub is meant  #-
        self.sock = s.socket()
    # -

    def __recvall(self, sock):
        data = b''
        while True:
              part = sock.recv(BUFF_SIZE)
              data += part
              if len(part) < BUFF_SIZE:
                 break
        return data

    def send_receive(self, message):
        # type: (list) -> str or int
        sock = socket.socket()  # create a socket
        sock.connect((self.host, self.port))  # connect to server
        sock.send(pickle.dumps(message))  # send some data
        result = pickle.loads(self.__recvall(sock))  # receive the response
        self.sock.close()  # close the connection
        return result
    

    @property
    def register(self):
        # type: () -> bool
        assert self.list_id is None  # -
        result = self.send_receive([REGISTER])
        self.list_id, registered_successfully = result[0], result[1]
        return registered_successfully

    def get_value(self):
        assert self.list_id is not None  # -
        return self.send_receive([GETVALUE, self.list_id])

    def append_data(self, peer_data_object):
        assert self.list_id is not None  # -
        result  = self.send_receive([APPEND, peer_data_object, self.list_id])
        return result

    def get_file_list(self):
        print(self.send_receive([ENUMERATE]))

    def register_chunk(self, peer_data_object):
       return self.send_receive([REGISTER_CHUNK, peer_data_object])
