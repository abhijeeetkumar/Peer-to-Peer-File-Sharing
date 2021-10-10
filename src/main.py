import pdb
import socket as socket
import argparse
import datetime
import time
import threading

from os import *
from server import *
from peer import *
#from validation import *

def build_server(port):
    print ("Welcome Server!!!")
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    print("Host name: ",hostname,ip_address,port)
    server = Server(socket, port, ip_address)
    server.run()


def search_and_download(ip,port):
      filename = input("Please enter filename you want to search for.\n")
      if len(filename) != 0:
         peer = Peer(socket, 0, "", port, ip)  # We don't have to set port or host for peer as it is not going to listen
         file_data = peer.search(filename, ip, port)
         peer_host, peer_port, download_size, download_it = show_result(file_data, filename)
         if download_it:
            peer.download_file([DOWNLOAD, filename], download_size, peer_host, peer_port)
         else:
            print ("Okay thank you for using our system.")
      else:
         print ("You cannot search for an empty string.")

def register_node(ip,port):
    print("Welcom Client for registration!!!")
    server_ip = ip
    server_port = port
    hostname = socket.gethostname()
    client_ip = socket.gethostbyname(hostname)
    #client_ip =    input("Enter your IP address in the following format XXX.XXX.XXX.XXX\n")
    #client_port = input("Enter your port number\n")
    peer = Peer(socket, server_port, client_ip, server_port, server_ip)
    PATH = input("Please enter the directory path of which you want to share its files.\n")
    
    try:
        shared_files = [f for f in listdir(PATH) if os.path.isfile(path.join(PATH, f))]
        shared_files_size = [os.path.getsize(path.join(PATH,f)) for f in listdir(PATH) if os.path.isfile(path.join(PATH, f))]
        if len(shared_files) != 0:
           shared_chunks = peer.preprocess_reg_file(PATH) #divide into chunks
           REGISTERED_SUCCESSFULLY = peer.data_object.register
           sharing_datetime = datetime.datetime.fromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S')
           data_object = dict(peer_port=server_port, peer_host=client_ip, shared_files=shared_files, shared_files_size=shared_files_size, shared_at=sharing_datetime, shared_chunks=shared_chunks)
           if REGISTERED_SUCCESSFULLY:
                DATA_INSERTED = peer.data_object.append_data(data_object)
                if DATA_INSERTED:
                   print ("Congratulations you have been registered successfully.\n" \
                          "[*] You will now be put to the listening state.\n" \
                          "[*] Started listening on", client_ip, ":", server_port)
                   i_thread = threading.Thread(target=peer.listen, args=(PATH,))
                   i_thread.start() #tpeer.listen(PATH)  # block until you receive request
                else:
                    print ("There was an error while inserting your data.")
        else:
           print ("You cannot share empty directory.")
    except Exception as exc:
        print("Caught exception: %s" %str(exc))

def add_new_shared_files(server_ip, server_port):
    print("not yet implemented")
    pass

def unshare_files(server_ip, server_port):
    print("not yet implemented")
    pass

def list_all_files(server_ip, server_port):
    peer = Peer(socket, 0, "", server_port, server_ip)
    peer.data_object.get_file_list() 

def build_client(server_ip, server_port):
    print ("Welcome Client!!!")
    while True: 
         choice = input("Enter 1 for registering the client with the"
                  "central server\n"
                  "Enter 2 for searching a file and downloading it"
                  "from the network.\n"
                  "Enter 3 for adding new folders in shared list.\n"
                  "Enter 4 for unsharing folders\n"
                  "Enter 5 to list all shared files in network\n")
         if choice == "1":
            register_node(server_ip,server_port)
         elif choice == "2":
            search_and_download(server_ip,server_port)
         elif choice == "3":
            add_new_shared_files(server_ip, server_port)
         elif choice == "4":
            unshare_files(server_ip, server_port)
         elif choice == "5":
            list_all_files(server_ip, server_port)
         else:
            pass 

def main():
    #parse args
    parser = argparse.ArgumentParser(description='P2P distributed system')
    parser.add_argument('-m','--mode', help='centralized server = 0, Peer = 1', required=True)
    parser.add_argument('-s', '--server-ip', help='IP address of centralized server. Expected format XXX.XXX.XXX.XXX')
    parser.add_argument('-p','--port-id', help='Port ID', type=int)
    parser.add_argument('-pt', '--peer-type', help='Register peer as listener or user', default=0)
    arguments = vars(parser.parse_args())
    #pdb.set_trace()
    
    port = 45000
    if arguments['port_id'] is not None:
      port = arguments['port_id']
    
    #Build node for the P2P system
    if arguments['mode'].lower() == 'server':
      print("Port: ",port)    
      build_server(port)
    elif arguments['mode'].lower() == 'client':
      if arguments['server_ip'] is None:
         print("Error!!! Please set \"server-ip\" to valid value")
         exit(1)
      ip = arguments['server_ip'] 
      build_client(ip, port)
    else:
      print ("Error!! Please use server/client as value for mode")
      exit(1)

if __name__ == '__main__':
    main()
