import socket
from threading import *

HOST = "127.0.0.1"
PORT = 60505
NEW_PEER = "new_peer"
LEFT_PEER = "left_peer"
BUFFER_SIZE = 1024
MANAGER_INFO = (HOST, PORT)

active_peers = set()
conn_peer = dict()


def broadcast_peers():
    global active_peers, manager_socket, conn_peer
    broadcast_msg = str(list(active_peers)).encode()
    for i in active_peers:
        conn_peer[i].sendall(broadcast_msg)


def communicate_with_peer(conn, client_addr):
    global active_peers
    try:
        while True:
            try:
                client_msg = conn.recv(BUFFER_SIZE)
                if client_msg == NEW_PEER.encode():
                    active_peers.add(client_addr)
                    print("New peer - {} added".format(client_addr))
                    broadcast_peers()
                elif client_msg == LEFT_PEER.encode():
                    active_peers.remove(client_addr)
                    print("Peer left - {}".format(client_addr))
                    del conn_peer[client_addr]
                    conn.close()
                    broadcast_peers()
            except:
                return
    except:
        print("Connection {} closed by error".format(client_addr))
        active_peers.remove(client_addr)
        del conn_peer[client_addr]
        conn.close()


manager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
manager_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
'''
the above thing we are using because if a client
gets disconnected server keeps some time that is
TIME_WAIT to connect back to it which server need 
to wait and so to avoid it at socket level we are 
specifying reuse address at the socket level
'''
manager_socket.bind(MANAGER_INFO)
manager_socket.listen(10)
print("Listening on port {}".format(PORT))

while True:
    try:
        conn, client_addr = manager_socket.accept()
        conn_peer[client_addr] = conn
        thread = Thread(target=communicate_with_peer,
                        args=(conn, client_addr), daemon=True)
        thread.start()
    except:
        print("Server Crashed")
        break
