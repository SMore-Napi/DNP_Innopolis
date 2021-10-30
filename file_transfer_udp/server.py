# Roman Soldatov
# B19-SD-01

# Server for UDP reliable file transfer
import time
from socket import socket, AF_INET, SOCK_DGRAM, timeout

IP_ADDR = "127.0.0.1"
PORT = 65432
BUF_SIZE = 100

RECEIVED_FILES = 0


def split_start_message(data):
    indices = []
    for index, el in enumerate(data):
        # Look for separators '|'
        if el == 124:
            indices.append(index)
    return data[indices[0] + 1:indices[1]].decode(), \
           data[indices[1] + 1:indices[2]].decode(), \
           data[indices[2] + 1:].decode()


def split_data_message(data):
    indices = []
    for index, el in enumerate(data):
        # Look for separators '|'
        if el == 124:
            indices.append(index)
    return data[indices[0] + 1:indices[1]].decode(), data[indices[1] + 1:]


def is_start_message(data):
    try:
        if data[0:1].decode() == "s":
            seqno0, extension, size = split_start_message(data)
            int(seqno0)
            str(extension)
            int(size)
            return True
    except (ValueError, UnicodeDecodeError):
        pass
    return False


def is_data_message(data):
    try:
        if data[0:1].decode() == "d":
            seqno, data_bytes = split_data_message(data)
            int(seqno)
            return True
    except (ValueError, UnicodeDecodeError):
        pass
    return False


with socket(AF_INET, SOCK_DGRAM) as s:
    s.bind((IP_ADDR, PORT))
    try:
        clients = {}
        while True:
            print(f'Active clients: {len(clients.keys())}')
            s.settimeout(1)
            try:
                data, addr = s.recvfrom(BUF_SIZE)
                recv_time = time.time()
                # Start new session
                if is_start_message(data):
                    seqno0, extension, size = split_start_message(data)
                    seqno0 = int(seqno0)
                    file_info = {'next_seqno': seqno0 + 1,
                                 'extension': str(extension),
                                 'expected_size': int(size),
                                 'file_binary': b'',
                                 'time': recv_time,
                                 'finished_session': False}
                    clients[addr[0]] = file_info
                    s.sendto(f"a|{seqno0 + 1}|{BUF_SIZE}".encode(), addr)
                # Continue receiving a file from a client
                elif is_data_message(data):
                    seqno, data_bytes = split_data_message(data)
                    next_seqno = clients[addr[0]]['next_seqno']
                    # If the server received a packet with expected seqno
                    if int(seqno) == next_seqno:
                        # Send ack message
                        next_seqno += 1
                        s.sendto(f"a|{next_seqno}".encode(), addr)
                        # Write info
                        clients[addr[0]]['time'] = recv_time
                        clients[addr[0]]['next_seqno'] = next_seqno
                        clients[addr[0]]['file_binary'] += data_bytes
                        # If the file was completely received
                        if len(clients[addr[0]]['file_binary']) == clients[addr[0]]['expected_size']:
                            clients[addr[0]]['finished_session'] = True
                            RECEIVED_FILES += 1
                            file_name = f'file {RECEIVED_FILES}.' + clients[addr[0]]['extension']
                            with open(file_name, 'wb') as f:
                                f.write(clients[addr[0]]['file_binary'])
                                print(f'Received file from {addr[0]}')
            except timeout:
                t = time.time()
                clients_to_delete = []
                # Check which session should be abandoned
                for client in clients:
                    file_info = clients[client]
                    last_tstamp = t - file_info['time']
                    # The server should hold the information related to the successfully finished file reception
                    # for some time (1.0s) before finally removing it.
                    if file_info['finished_session'] and last_tstamp >= 1:
                        clients_to_delete.append(client)
                    # If the client isn’t active for very long (more than 3s) and the associated file reception session
                    # isn’t yet finished, then the server should abandon this session
                    # and remove everything related to this station.
                    elif not file_info['finished_session'] and last_tstamp >= 3:
                        clients_to_delete.append(client)
                # Remove such clients
                for client in clients_to_delete:
                    clients.pop(client, None)
    except KeyboardInterrupt:
        print("Keyboard interrupt, server is shutting down.")
