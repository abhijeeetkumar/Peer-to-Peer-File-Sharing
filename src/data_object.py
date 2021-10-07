import pickle
from constants import *  # -


# -
class DataObject:
    def __init__(self, s, host, port, list_id=None):  # -
        self.host = host  # address of server hosting lists        #-
        self.port = port  # the port it will be listening to       #-
        self.list_id = list_id  # the list for which this stub is meant  #-
        self.sock = s.socket()

    # -
    
    def send_receive(self, message):
        # type: (list) -> str or int
        #sock = self.sock  # create a socket
        self.sock.connect((self.host, self.port))  # connect to server
        self.sock.send(pickle.dumps(message))  # send some data
        result = pickle.loads(self.sock.recv(1024))  # receive the response
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
        return self.send_receive([APPEND, peer_data_object, self.list_id])
