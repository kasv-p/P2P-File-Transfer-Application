import socket
from threading import *
import sys
import os

''' need to handle error like req file before asking the list/ threading
to a peer which dont have the file  change sharable files list '''
MANAGER_IP = "127.0.0.1"
MANAGER_PORT = 60505
MANAGER_INFO = (MANAGER_IP, MANAGER_PORT)
NEW_PEER = "new_peer"
LEFT_PEER = "left_peer"
REQ_FILE = "req"
HAVE = "have"
NOT_HAVE = "not have"
SEND_FILE = "file"
END_FILE = b"eof"
BUFFER_SIZE = 10240000
PEER_IP = "127.0.0.1"
HELP_STRING = "\nreq <filename> to request a file\n\
left_peer to leave from the network\n\
help to get list of commands\n\
"
PEER_PORT = int(sys.argv[1])
PEER_INFO = (PEER_IP, PEER_PORT)
PEER_DIRECTORY = sys.argv[2]
HELP = "help"
NO = "n"
NO_CHUNK = -1
PATH = os.path.join(os.getcwd(), PEER_DIRECTORY)
active_peers = []
sharable_files = os.listdir(PATH)
file_data = dict()


def receive_from_server():

    global active_peers, peer_connect_socket

    try:
        while True:
            manager_msg = peer_connect_socket.recv(BUFFER_SIZE)
            active_peers = eval(manager_msg.decode())
    except:
        return


def communicate_peer(conn, addr):
    try:
        while True:

            peer_msg = conn.recv(BUFFER_SIZE).decode()
            peer_msg = peer_msg.split()

            if len(peer_msg) == 2 and peer_msg[0] == REQ_FILE:
                required_file_name = peer_msg[1]
                if required_file_name in sharable_files:
                    conn.sendall(HAVE.encode())
                else:
                    conn.sendall(NOT_HAVE.encode())
                conn.close()

            elif len(peer_msg) == 4 and peer_msg[0] == SEND_FILE:

                file_name = peer_msg[1]
                chunk_number = int(peer_msg[2])
                no_chunks = int(peer_msg[3])
                f = open(os.path.join(PATH, file_name), "rb")
                file_data_bytes = f.read()
                f.close()

                lower_limit = (chunk_number)*(len(file_data_bytes))//no_chunks
                upper_limit = (chunk_number+1) * \
                    (len(file_data_bytes))//no_chunks

                start = lower_limit
                while start < upper_limit:
                    conn.sendall(file_data_bytes[start:start+BUFFER_SIZE])
                    start += BUFFER_SIZE
                conn.sendall(END_FILE)
                conn.close()

            break
    except:
        return


def listen_to_peer():
    try:
        global peer_socket
        while True:
            conn, addr = peer_socket.accept()
            thread = Thread(target=communicate_peer,
                            daemon=True, args=(conn, addr))
            thread.start()
    except:
        return


def file_thread(to_connect_peer_info, i, req_msg, no_peers):
    # try:
    global file_data
    temp_connect_socket = socket.socket(
        socket.AF_INET, socket.SOCK_STREAM)
    temp_connect_socket.setsockopt(
        socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    temp_connect_socket.connect(to_connect_peer_info)

    req_msg = req_msg+" "+str(i)+" "+str(no_peers)
    temp_connect_socket.sendall(req_msg.encode())
    data_recv = temp_connect_socket.recv(BUFFER_SIZE)
    data_in_bytes = b""
    while data_recv != END_FILE:
        data_in_bytes += data_recv
        data_recv = temp_connect_socket.recv(BUFFER_SIZE)

        if len(data_recv) < BUFFER_SIZE:
            try:
                if data_recv[-3:].decode() == END_FILE.decode():
                    data_in_bytes += data_recv[:-3]
                    break
            except:
                continue
        if len(data_recv) == 0:
            break
    file_data[i] = data_in_bytes
    temp_connect_socket.close()


peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
peer_socket.bind(PEER_INFO)
peer_socket.listen(10)


peer_connect_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
peer_connect_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
peer_connect_socket.bind(PEER_INFO)
peer_connect_socket.connect(MANAGER_INFO)
peer_connect_socket.sendall(NEW_PEER.encode())

thread1 = Thread(target=receive_from_server, daemon=True, args=())
thread1.start()
thread2 = Thread(target=listen_to_peer, daemon=True, args=())
thread2.start()

print(HELP_STRING)

while True:

    ask = input("> enter cmd - ").split()

    if len(ask) == 2 and ask[0] == REQ_FILE:

        peers_found = []
        file_name = ask[1]
        if file_name in sharable_files:
            yesorno = input(
                "> A file with same name already exists. Do you want to continue ? (Y/N) ")
            if yesorno.lower() == NO:
                continue
        for i in active_peers:
            if i != PEER_INFO:
                to_connect_peer_info = i
                temp_connect_socket = socket.socket(
                    socket.AF_INET, socket.SOCK_STREAM)
                temp_connect_socket.setsockopt(
                    socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                temp_connect_socket.connect(to_connect_peer_info)
                ask_msg = REQ_FILE+" "+file_name
                temp_connect_socket.sendall(ask_msg.encode())
                conn_peer_msg = temp_connect_socket.recv(
                    BUFFER_SIZE).decode()
                if conn_peer_msg == HAVE:
                    peers_found.append(to_connect_peer_info)
                temp_connect_socket.close()

        if len(peers_found) == 0:
            print("No peers to share the file try after some time")
            continue

        req_msg = ' '.join([SEND_FILE, file_name])

        need_to_join = []

        no_peers = len(peers_found)

        for i in range(len(peers_found)):
            to_connect_peer_info = peers_found[i]
            thread = Thread(target=file_thread, daemon=True, args=(
                to_connect_peer_info, i, req_msg, no_peers))
            need_to_join.append(thread)
            thread.start()

        for i in need_to_join:
            i.join()

        file_data = {i: j for i, j in sorted(file_data.items())}
        if len(file_data) == no_peers:
            f = open(os.path.join(PATH, file_name), "wb")
            for i in file_data:
                f.write(file_data[i])
            f.close()
            print("All chunks of {} are received and saved with the same file name".format(
                file_name))
            sharable_files = os.listdir(PATH)

        elif len(file_data) != 0:

            print("All chunks not received file transfer failed trying again")

            need_to_join = []
            missing_chunk_numbers = [
                i for i in file_data.keys() if i not in range(no_peers)]

            while len(file_data) == no_peers or len(file_data) == 0:
                for i in range(len(peers_found)):
                    to_connect_peer_info = peers_found[i]
                    for missed_chunk in missing_chunk_numbers:
                        thread = Thread(target=file_thread, daemon=True, args=(
                            to_connect_peer_info, missed_chunk, req_msg, no_peers))
                        need_to_join.append(thread)
                        thread.start()
                    if len(file_data) == no_peers or len(file_data) == 0:
                        break

            for i in need_to_join:
                i.join()

        elif len(file_data) == 0:

            print(
                "Peers might be there before, but got diconnected while transferring file so please try after sometime.")

        file_data.clear()

    elif ask[0] == LEFT_PEER:
        peer_connect_socket.sendall(LEFT_PEER.encode())
        peer_connect_socket.close()
        peer_socket.close()
        break
    elif ask[0] == HELP:
        print(HELP_STRING)
    else:
        print("invalid command")
print("connection closed. Bye...")
