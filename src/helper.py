import os
from constants import *
from collections import defaultdict

def show_result(result, filename, _=None):
    # type: (list, str) -> [any,any,bool]
    chunkid_to_addresses  = defaultdict(list)
    if result[0]:
        print ("File", filename, "was found in the following one or more peers. Peer/s details are:\n")
        for key in result[1]:
            value = result[1].get(key)
            print ("Peer ID:", key, "\n")
            print ("Peer port:", value['peer_port'], "\n")
            print ("Peer host:", value['peer_host'], "\n")
            print_chunks(value['shared_chunks'], filename, chunkid_to_addresses, value)
            print ("File shared at:", value['shared_at'], "\n")
            print ("-------------------------------------")
        download_it = input("Do you want to download it (Y/N):\n")
        download_it = (download_it.strip()).lower()
        if download_it == "y":
            return chunkid_to_addresses, True
        elif download_it == 'n':
            return _, False  # When user refuses to download it return any,any,false
        else:
            print ("Invalid Choice")
            return _, False
    else:
        print ("File", filename, "was not found!")

def get_file_id(file_list, filename):
    for file_id, file_name in enumerate(file_list):
       if filename == file_name:
          break

    return file_id

def print_chunks(shared_chunks, filename, chunkid_to_addresses, data):
    chunk_filename = [value.split('/')[-1] for value in shared_chunks.get(filename)]
    print("Chunks available: ",chunk_filename, "\n")
    for chunkid in chunk_filename:
       chunkid_to_addresses[chunkid].append(':'.join([data['peer_host'], str(data['peer_port'])]))

def get_chunk_path(tmp_dir, filename, chunkid):
    parent = os.path.join(tmp_dir, filename)
    postfix = chunkid
    if not os.path.exists(parent):
       os.system('mkdir -p {}'.format(parent))
    if isinstance(chunkid, int):
       postfix = str(chunkid) + '.chunk'
    return os.path.join(parent, postfix)

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

def send_file(conn, data, tmp_dir):
    filename = data[1]
    filepath = os.path.join(tmp_dir, filename)
    print(data)
    for f in list(data[2:]):
       path_to_file = os.path.join(filepath, f)
       with open(path_to_file, 'rb') as file_to_send:
          for data in file_to_send:
             conn.sendall(data)

    print('Done sending')
    conn.close()
