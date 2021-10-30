# Roman Soldatov
# B19-SD-01

# Client for UDP calculator

from socket import socket, AF_INET, SOCK_DGRAM

DEST_IP_ADDR = "127.0.0.1"
DEST_PORT = 65432
PORT = 65433
BUF_SIZE = 100000

with socket(AF_INET, SOCK_DGRAM) as s:
    s.bind(("localhost", PORT))
    try:
        while True:
            command = input("Input command for calculation: ")
            if command.lower() == "quit":
                print("User has quit.")
                break
            s.sendto(command.encode(), (DEST_IP_ADDR, DEST_PORT))
            data, addr = s.recvfrom(BUF_SIZE)
            print(f"Result: {data.decode()}\n")
    except KeyboardInterrupt:
        print("User has quit.")
