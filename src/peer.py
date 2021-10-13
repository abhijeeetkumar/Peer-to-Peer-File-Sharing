from data_object import *
from helper import *
import random
import math
import threading
import datetime
import time
from queue import PriorityQueue 

class Peer:
    def __init__(self, s, port, host, server_port, server_host):
        # type: (int, str) -> None
        self.host = host  # this machine
        self.port = port  # port it will listen to
        self.sock = s.socket()  # socket for incoming calls
        self.sock.bind((self.host, self.port))  # bind socket to an address
        self.sock.listen(5)  # max num connections
        self.data_object = DataObject(s, server_host, server_port)
        self.tmp_dir = os.path.join(os.path.join(os.getcwd(), 'temp'), socket.gethostname())
        self.is_listening  = False 
        self.am_choking = defaultdict(lambda:True)  #Choking - Unchoking
        self.am_interested = defaultdict(lambda:False)
        self.peer_choking = defaultdict(lambda:True)
        self.peer_interested = defaultdict(lambda:False)

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

    def download_chunk_thread(self, host, port, message, dir_path, chunk_ids):
        s = socket.socket()
        s.connect((host,int(port)))

        #since message is mutuable (pass by reference in C), so all thread will see changes 
        #thus creating a new one
        new_message = [message[0], message[1]]
        new_message.append(chunk_ids)
        #print(new_message)
        s.send(pickle.dumps(new_message))  # send some data 

        with open(os.path.join(dir_path, chunk_ids), 'wb') as file_to_write:
             data = b''
             while True:
                   part = s.recv(BUFF_SIZE)
                   data += part
                   if len(data) > BYTES_PER_CHUNK:
                      break
                   if not part:
                      break 
             file_to_write.write(data)
        file_to_write.close()

        print("downloaded", chunk_ids, "from", host,":", port)
        filename = dir_path.split("/")[-1]
        chunk_path = []
        chunk_path.append(str(os.path.join(dir_path,chunk_ids)))
        shared_chunks = {filename:chunk_path}
        shared_files_size = [os.path.getsize(f) for f in chunk_path]
        sharing_datetime = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')
        peer_data_object = dict(peer_port=self.port, peer_host=self.host, shared_at=sharing_datetime, shared_files=filename,
                                shared_files_size=shared_files_size, shared_chunks=shared_chunks)
        IS_SUCCESS =self.data_object.register_chunk(peer_data_object)
        if IS_SUCCESS:
           print("Registered as source for chunk id:", chunk_ids)
           i_thread = threading.Thread(target=self.listen, args=(dir_path,))
           i_thread.start()
        s.close()

    def download_file(self, message, chunkid_to_addresses):
        downloads_dir_path = os.path.join(os.path.join(os.getcwd(), 'downloads'), socket.gethostname())  
        filename = message[1]  # requested filename from the server
        if not os.path.exists(downloads_dir_path):
            os.makedirs(downloads_dir_path)

        downloaded_filename = os.path.join(downloads_dir_path, "downloaded_" + filename)

        chunkids = list(chunkid_to_addresses.keys())
        #print(chunkids)

        #host, port = list(chunkid_to_addresses.values())[0][0].split(":")
        #self.download_chunk_thread(host,port,message,os.path.join(self.tmp_dir, filename), chunkids)

        download_queue = PriorityQueue() #rarest_first by len(value())
        counter = 0
        for key, value in chunkid_to_addresses.items(): 
           download_queue.put((len(value), counter, {
                'addresses': value,
                'filename' : filename,
                'chunkid'  : key
           }))
           counter += 1

        threads = []
        while not download_queue.empty():
           entry = download_queue.get()

           #print(list(entry[2]['addresses']))
           lst = list(entry[2]['addresses'])
           for alive_peer in random.sample(lst,len(lst)): #fault tolerance: if node exits, download from other peer
               try:
                 sock = socket.socket()
                 host, port = alive_peer.split(":")
                 sock.connect((host, int(port)))
                 sock.send(pickle.dumps([PING]))
                 sock.close()
                 break
               except Exception as e:
                 print(alive_peer, "is dead! Trying another peer %s" %str(e))
           host, port = alive_peer.split(":")

           self.am_interested[host] = True
           self.am_choking[host] = False
           self.peer_choking[host] = False    #Since we are not maintaning shared memory for all thread
           Peer.send_to(host, int(port), [UNCHOKE])
           #print("unchoking ", host)

           filename = entry[2]['filename']
           chunkid = entry[2]['chunkid'] 

           dir_path = os.path.join(self.tmp_dir, filename)
           if not os.path.exists(dir_path):
              os.makedirs(dir_path)
           ignore_flag = False
           for chunkid_exsisting in os.listdir(dir_path):  #fault tolerance: file already downloaded
              if chunkid == chunkid_exsisting:
                 print(chunkid, "already downloaded.") 
                 ignore_flag = True
                 break
           if ignore_flag == True:
              continue  

           args = (host, port, message, dir_path, chunkid)
           t = threading.Thread(target=self.download_chunk_thread, args = args)

           while not (self.am_interested[host] == True and self.peer_choking[host] == False):
              print("Entering sleep mode in download. Host",host,"  ",self.am_interested[host],"  ", self.peer_choking[host])
              time.sleep(5) 
           t.start()
           threads.append(t)
           self.am_interested[host] = False 

        for t in threads:
           t.join()

        combine_chunks_to_file(self.tmp_dir, downloaded_filename, filename, chunkids)

        print('Successfully get the file')
        print('connection closed')

    @staticmethod
    def send_receive(message, host, port):
        # type: (list) -> str or int
        sock = socket.socket()  # create a socket
        #print("Host: ",host," Peer: ",port)
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
        #print("Host: ",host," Port: ",port)
        sock.connect((host, port))  # connect to server (blocking call)
        sock.send(pickle.dumps(data))  # send some data
        sock.close()

    def listen(self, PATH):
        if self.is_listening == True:
           pass

        self.is_listening = True 
        while True:
            (conn, addr) = self.sock.accept()
            now = datetime.datetime.fromtimestamp(int(time.time()))
            print ("[*] Got a connection from ", addr[0], ":", addr[1]," at:",now.strftime('%Y-%m-%d %H:%M:%S'))
            data = self.__recvall(conn)
            request = pickle.loads(data)  # unwrap the request
            if request[0] == DOWNLOAD:
                while not (self.peer_interested[addr[0]] == True and self.am_choking[addr[0]] == False):
                     #print(" entering sleep mode in download. ",addr[0])
                     time.sleep(5)
                send_file(conn, request, self.tmp_dir)
                self.peer_interested[addr[0]] = False 
            if request[0] == PING:
                self.peer_interested[addr[0]] = True
                #print("interested by", addr[0])
                self.am_choking[addr[0]] = False #should unchoke only after recieveing chunk
                #Peer.send_to(addr[0], addr[1]-2, [UNCHOKE])
                #print("unchoking ", addr[0])
            if request[0] == CHOKE:
               self.peer_choking[addr[0]] = True
               print("choked by", addr[0])
            if request[0] == UNCHOKE:
               self.peer_choking[addr[0]] = False
               print("unchoked by", addr[0],  self.peer_choking[addr[0]]) 


