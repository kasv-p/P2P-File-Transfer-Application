# P2P-File-Transfer-Application

Abstract
-------------------------

Here, manager broadcasts the active peers in the p2p network.
When a peer joins the networks it pings the manager and manager send the active peers list

When a peer requests a file peers with that file will response with a message called "have" when the peer receives the "have" message the requesting peer connects with all the peers who have the file and send them parallely (implemented using threads) via chunks.

Explaining Code Files
--------------------------

<b>Manager Code</b>

Functions are broadcast_peers, communicate_peer and main function

`broadcast_peers()`

send active_peers list to all the peers which are connected to the manager.

`communicate_peer()`

This function receives the "new_peer" message from the peer who connected now and with that information the peer address is added to the active peers list maintained by the manager. When a "left_peer" message is received fromm the peer remove the peer from active_peers list and delete from the dictionary.

`main function - main()`

Here, a manager socket is created and it is bind to the ip adress and a particular port number which will be known to the peer being connected to this manager also. Here, a active list is maintained and also a dictionary is maintained which maps from client address to conn retunted by socket on accepting. When, a peer leaves it sends a message "left_peer" which is noticed by manager and removes the peer from active peers list and also from the dictionary. The same happpens if a peer leaves by any connection failure also.

<b>Peer Code</b>

Functions are receive_from_server, communicate_peer, listen_to_peer, file_thread and main function.

`receive_from_server()`

This function receives active peers list from the manager and updates the list whenever the manager broadcast the list that means when a new peer added or a peer left.

`listen_to_peer()`

This function acepts any connectiosn that recheases to this socket and creates a thread whenever a peer is connected to this socket and the thread created executes the communicate_peer function.

`communicate_peer()`

This function receives message from the peer. Whenever a message like "req <file name>" is received then it checks if the file exists in the list os sharable files if yes the it will send a message "have" to the requesting peer and "not have" message if there is no such file in the sharable files list of that peer.
<br>
Also if it is requested to send a chunk of specific file it divides the file into equal chunks and send the chunk only that is requested from the whole file.
  <br>
Here, lower limit of the chunk is calculated using the formula (chunk*number)*(len(file*data_bytes))//no_chunks and upper limit is (chunk_number+1)*(len(file_data_bytes))//no_chunks and it sends the file_data_bytes[lower_limit:upper_limit]. Here, the number of chunks will be equal to the number of peers present in the network haivng the requested file in their sharable files list.
  <br>
It also sends the eof file message as the requested chunk is further divided into chunks of size equal to BUFFER_SIZE and at last it sends eof message to tell the chunks to be sent are done and it is the end of the chunk being sent by it. <br>

`file_thread()`

This function receives the data from the peer which is sending the file and keeps the data in file_data dictionary. Later closes the temporary socket connection made to fetch the file. This is a helper function to create threads on fetching a file in parallel.<br>
This also reads the chunks of data being received till the eof message is sent to the requesting client. 

`main function - main()`

creates a peer_socket to listen from any other peers and listen from manager. <br>
Here, these are 2 different threads which will run from start of the main function. Also send "new_peer" message automatically to manager to update the active_peers list on the manager side. <br>When a message like "left_peer" is given as input all connections from this and to this socket are closed. When a message like "req <filename>" is given to the peer it creates dummy sockets to connect to the peers which are present int the active peers list and first communicate with "have" and "not have" messages. <br>The peer with files will be added to the peers_found list and later the socket communicates with the peers who sent the "have" message. It created threads to get file data parallely on function file_thread which receives data from the peer with dile and keeps the data in a dictionary in file_data in which keys are peer index numbers in the peers_found list nad the data will be value for the respective peer key. <br> Later the peer need to join in the threads created to fetch the files as then only all the bytes will be received properly from the peers who sent the file chunks.<br> Later the dictionary is sorted according to the keys and merged by adding all the bytes after sorting the keys in the file_data dictionary and then created new file and write data to the file in the directory of the requested peer.<br> Also the sharable files list is updated on receiving a file fully. In case if a peer gets disconnected in between file transfer missing chunk numbers are found and request those all chunks from diff peers which are present in peers_found list already if none of them are present then the file can't be shared and need to be requested later that is after some time.

How to run ?
--------------------------

python manager.py - This command is to run the manager.py file which will have the peer info. Manager program runs in a while loop infinitely.

python peer.py <PORT_NUM> <DIR_NAME> - This command is to run the peer python file which takes port number and directory name as command line arguments. 
<br>  
The port number given is used to bind the peer socket to that port number, the dir with the name DIR_NAME is given to get the sharable files of the peer. This list will be updated on successfully receiving a eew file from other peer.
<br>
peer will be asked input continuously in a while loop such that when a peer want to leave peer need to enter message left_peer and  
to request a file peer need to enter the command req <file_name>.

Program structure
--------------------------

    For manager code

        bind, listen

        while loop -> conn, client_address, start a thread to communicate

        If added call the function broadcast_peers, if left also call the function broadcast_peers.

    For peer code

        2 threads

        1. connect to manager as a client (function=receive_from_server) update per process active_peers list
        2. A thread to accept connections from peers
        (function=listen_to_peer) acting like a server to other peers on file request.
            1. If have file in sharable list send have else send not have.
            2. If requested a chunk send that part from the file according to the chunk requested from the requesting peer.

        Take input in a while loop

        if left_peer

        1. send to manager that the peer is leaving.
        2. close the connection socket between manager and the peer.

        if req file_name

        1. send req to file and add the peers who have file to peers_found list.
        2. create and join on threads (function=file_thread) to get the file requested from the pther peers and merge it.

        help command shows the list of commands available to the the peer or client who is using the protocol.

    A newly arrived peer, managing when a peer leaves - communicate_with_peer(conn, client_addr)
    Manager periodically broadcasts - broadcast_peers()

    receiving file from peer - file_thread(to_connect_peer_info, i, req_msg, no_peers)
    listening to other peers - listen_to_peer(), communicate_peer()
    getting list of active peers when broadcasted - receive_from_server() 

    dividing chunks according to the buffer size along with considering the only part need to be divided

    lower_limit = (chunk_number)*(len(file_data_bytes))//no_chunks
    upper_limit = (chunk_number+1) * \
        (len(file_data_bytes))//no_chunks

    start = lower_limit
    while start < upper_limit:
        conn.sendall(file_data_bytes[start:start+BUFFER_SIZE])
        start += BUFFER_SIZE
    conn.sendall(END_FILE)
    conn.close()

    active_peers - maintain list of peers which are active in the p2p network.
    file_data - dictionary of chunk and the data received.
    all messages used to communicate are mentioned in the top of the peer python file. 



Note - conditions that should be taken care is when chunk size of the file to be transferred is greater than BUFFER SIZE then one need to send the file in the order each sending data of length BUFFER SIZE.
Also there is a EOF message sent to ensure that the sending peer has sent all the chunk data fully to the requested peer.

link of demo video url - https://drive.google.com/file/d/1ttCQWBx1OsIs4Ms2twVRI1oBkVHIkeDi/view?usp=sharing
