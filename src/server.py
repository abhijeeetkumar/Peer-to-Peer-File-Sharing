from threading import *
import pickle
from constants import *
from controller import *

class Server:
    def __init__(self, s, port=0, host=0, max_num_connections=5):
        self.host = host  # this machine
        self.semaphore = Semaphore(max_num_connections)  # Handling threads synchronization for critical sections.
        self.port = int(port)  # the port it will listen to
        self.sock = s.socket()  # socket for incoming calls
        self.sock.bind((self.host, self.port))  # bind socket to an address
        self.sock.listen(max_num_connections)  # max num of connections
        self.setOfLists = {}  # init: no lists to manage
        print ("[*] Started listening on", self.host, ":", self.port)

    def __recvall(self, sock):
        data = b''
        while True:
              part = sock.recv(BUFF_SIZE)
              data += part
              if len(part) < BUFF_SIZE:
                 break
        return data


    def run(self):
        while True:
            (conn, addr) = self.sock.accept()  # accept incoming call
            print ("[*] Got a connection from ", addr[0], ":", addr[1])
            data = self.__recvall(conn)  # fetch data from peer
            request = pickle.loads(data)  # unwrap the request
            print ("[*] Request after unwrap", request)
            if request[0] == REGISTER:  # create a list
                self.semaphore.acquire()
                register(conn, self.setOfLists)
                self.semaphore.release()

            elif request[0] == APPEND:  # append request
                self.semaphore.acquire()
                append(conn, request, self.setOfLists)
                self.semaphore.release()

            elif request[0] == GETVALUE:  # read request
                list_id = request[1]  # fetch list_id
                result = self.setOfLists[list_id]  # get the elements
                conn.send(pickle.dumps(result))  # return the list
            # -
            elif request[0] == STOP:  # request to stop
                print (self.setOfLists)
                conn.close()  # close the connection  #-
                break  # -
            elif request[0] == SEARCH:
                #self.semaphore.acquire() - i dont need for search
                found_boolean, file_object = search(request[1], self.setOfLists)
                if found_boolean:
                    conn.send(pickle.dumps([found_boolean, file_object]))
                else:
                    conn.send(pickle.dumps([found_boolean]))
                #self.semaphore.release()
            elif request[0] == ENUMERATE:
               result_file_list = file_list(self.setOfLists)
               conn.send(pickle.dumps(result_file_list))
