import os
from constants import *

def show_result(result, filename, _=None):
    # type: (list, str) -> [any,any,bool]
    if result[0]:
        print ("File", filename, "was found in the following one or more peers. Peer/s details are:\n")
        for key in result[1]:
            value = result[1].get(key)
            print ("Peer ID:", key, "\n")
            print ("Peer port:", value['peer_port'], "\n")
            print ("Peer host:", value['peer_host'], "\n")
            print ("File shared at:", value['shared_at'], "\n")
            print ("-------------------------------------")
        download_it = input("Do you want to download it (Y/N):\n")
        download_it = (download_it.strip()).lower()
        if download_it == "y":
            if len(result[1]) > 1:  # Making sure there are more than one registered peer has the file.
                peer_id = input("Please specify Peer ID\n")
                try:
                    peer_id = int(peer_id)
                    if peer_id in result[1]:
                        peer_host = result[1].get(peer_id)['peer_host']
                        peer_port = result[1].get(peer_id)['peer_port']
                        return peer_host, peer_port, True
                    else:
                        return _, _, False
                except ValueError:
                    return _, _, False

            else:
                # Dictionary contains only one element. So we retrieve its host and port
                peer_host = list(result[1].values())[0]['peer_host']
                peer_port = list(result[1].values())[0]['peer_port']
                return peer_host, peer_port, True
        elif download_it == 'n':
            return _, _, False  # When user refuses to download it return any,any,false
        else:
            print ("Invalid Choice")
            return _, _, False
    else:
        print ("File", filename, "was not found!")

def get_chunk_path(tmp_dir, filename, chunkid):
    parent = os.path.join(tmp_dir, filename)
    if not os.path.exists(parent):
       os.system('mkdir -p {}'.format(parent))
    return os.path.join(parent, str(chunkid) + '.chunk')

def split_file_into_chunks(tmp_dir, filepath):
    filename = filepath.split('/')[-1]
    listOfChunks = []
    with open(filepath, 'rb') as f:
         for chunkid, chunk in enumerate(iter(lambda: f.read(BYTES_PER_CHUNK), b'')):
             local_chunk_path = get_chunk_path(tmp_dir, filename, chunkid)
             listOfChunks.append(local_chunk_path)
             with open(local_chunk_path, 'wb') as g:
                  g.write(chunk)
    return listOfChunks 

def combine_chunks_to_file(tmp_dir, destination, filename, chunkids):
    with open(destination, 'wb') as f:
         for chunkid in chunkids:
             with open(get_chunk_path(tmp_dir, filename, chunkid), 'rb') as g:
                  f.write(g.read())

def send_file(conn, data, PATH):
    file_path = PATH
    filename = data[1]
    path_to_file = os.path.join(file_path, filename)
    with open(path_to_file, 'rb') as file_to_send:
        for data in file_to_send:
            conn.sendall(data)
    print('Done sending')
    conn.close()
