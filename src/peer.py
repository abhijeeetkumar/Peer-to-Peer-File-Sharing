from data_object import *
from helper import *

import math

class Peer:
    def __init__(self, s, port, host, server_port, server_host):
        # type: (int, str) -> None
        self.host = host  # this machine
        self.port = port  # port it will listen to
        self.sock = s.socket()  # socket for incoming calls
        self.sock.bind((self.host, self.port))  # bind socket to an address
        self.sock.listen(2)  # max num connections
        self.data_object = DataObject(s, server_host, server_port)
        self.tmp_dir = os.path.join(os.path.join(os.getcwd(), 'temp'), socket.gethostname())
        if not os.path.exists(self.tmp_dir):
           os.makedirs(self.tmp_dir)

    @staticmethod
    def __recvall(sock):
        data = b''
        while True:
              part = sock.recv(BUFF_SIZE)
              data += part
              if len(part) < BUFF_SIZE:
                 break
        return data

    def preprocess_reg_file(self, file_dir):
         return_data = {}
         for f in os.listdir(file_dir):
             return_data.update({f:split_file_into_chunks(self.tmp_dir, os.path.join(file_dir, f))})

         return return_data

    def search(self, filename, host, port):
        result = self.send_receive([SEARCH, filename], host, port)
        return result

    def download_file(self, message, file_size, host, port):
        s = socket.socket()
        s.connect((host, port))  # connect to server
        s.send(pickle.dumps(message))  # send some data
        downloads_dir_path = os.path.join(os.path.join(os.getcwd(), 'downloads'), socket.gethostname())  
        filename = message[1]  # requested filename from the server
        if not os.path.exists(downloads_dir_path):
            os.makedirs(downloads_dir_path)

        downloaded_filename = os.path.join(downloads_dir_path, "downloaded_" + filename)

        chunkids = range(math.ceil(file_size/BYTES_PER_CHUNK))
        for chunkid in chunkids:
           with open(get_chunk_path(self.tmp_dir, filename, chunkid), 'wb') as file_to_write:
               data = s.recv(BYTES_PER_CHUNK)
               file_to_write.write(data)
           file_to_write.close()

        combine_chunks_to_file(self.tmp_dir, downloaded_filename, filename, chunkids)

        s.close()
        print('Successfully get the file')
        print('connection closed')

    @staticmethod
    def send_receive(message, host, port):
        # type: (list) -> str or int
        sock = socket.socket()  # create a socket
        sock.connect((host, port))  # connect to server
        sock.send(pickle.dumps(message))  # send some data
        result = pickle.loads(Peer.__recvall(sock))  # receive the response - TODO: pickle.loads() can only work for 4096B object
        sock.close()  # close the connection
        return result

    @staticmethod
    def send_to(host, port, data):
        # type: (str, str, list) -> None
        """
        :rtype: None
        """
        sock = socket.socket()
        sock.connect((host, port))  # connect to server (blocking call)
        sock.send(pickle.dumps(data))  # send some data
        sock.close()

    def listen(self, PATH):
        while True:
            (conn, addr) = self.sock.accept()
            print ("[*] Got a connection from ", addr[0], ":", addr[1])
            data = self.__recvall(conn)
            request = pickle.loads(data)  # unwrap the request
            if request[0] == DOWNLOAD:
                send_file(conn, request, self.tmp_dir)
