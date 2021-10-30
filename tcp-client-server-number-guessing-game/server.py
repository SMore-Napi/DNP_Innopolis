# Roman Soldatov
# B19-SD-01

# Server for the TCP number guessing game.
# Server application can serve up to two clients at the same time
# For each new client the server creates a new thread which binds to a new socket

import random
import sys
from socket import socket, AF_INET, SOCK_STREAM, timeout, gaierror, SOL_SOCKET, SO_REUSEADDR
from threading import Thread

IP_ADDR = '127.0.0.1'
BUF_SIZE = 1024
MAX_ATTEMPTS = 5
TIMEOUT_CLIENT = 5


class PortManager:
    def __init__(self, port, max_active_clients):
        self.available_ports = list(range(port + 1, port + max_active_clients + 1))

    def pop_port(self):
        return self.available_ports.pop() if len(self.available_ports) > 0 else None

    def push_port(self, port):
        self.available_ports.append(port)


class RangeNumbersException(Exception):
    pass


def validate_command_line_input():
    if len(sys.argv) == 2:
        try:
            int(sys.argv[1])
            return
        except ValueError:
            pass
    print("Usage example: python ./server.py <port>")
    sys.exit()


def get_guess_number(message):
    """
    Generates random number from specified range
    :raise RangeNumbersException if numbers range is not valid
    """
    try:
        min_number, max_number = [int(x) for x in message.split(" ")]
        if min_number >= max_number:
            raise RangeNumbersException
        return random.randint(min_number, max_number)
    except ValueError:
        raise RangeNumbersException


def start_game(ip, port):
    """
    Start the guess number game
    """
    with socket(AF_INET, SOCK_STREAM) as s_thread:
        s_thread.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            s_thread.bind((ip, port))
            s_thread.settimeout(TIMEOUT_CLIENT)
            try:
                s_thread.listen()
                connection, address = s_thread.accept()
                try:
                    connection.send("welcome|".encode())
                    message = connection.recv(BUF_SIZE).decode()
                    guess_number = get_guess_number(message)
                    attempts = MAX_ATTEMPTS
                    connection.send(f"a|{attempts}".encode())
                    while attempts > 0:
                        number = int(connection.recv(BUF_SIZE).decode())
                        if number == guess_number:
                            connection.send("finish|win".encode())
                            break
                        attempts -= 1
                        if attempts <= 0:
                            connection.send("finish|lose".encode())
                            break
                        else:
                            code = "gr" if number < guess_number else "le"
                            connection.send(f"{code}|{attempts}".encode())
                except (RangeNumbersException, ValueError, ConnectionResetError):
                    pass
                connection.close()
            except timeout:
                print("Client didn't connect")
        except (gaierror, ConnectionRefusedError, OverflowError):
            print(f"Error while binding to the specified port: {port}")
    port_manager.push_port(port)


def handle_new_connection():
    """
    Reject or accept new client
    """
    new_port = port_manager.pop_port()
    if new_port is None:
        print("The server is full")
        return "finish|full"
    else:
        print("Client connected")
        t = Thread(target=start_game, args=(IP_ADDR, new_port))
        t.start()
        return f"port|{new_port}"


if __name__ == "__main__":
    validate_command_line_input()
    SERVER_PORT = int(sys.argv[1])
    with socket(AF_INET, SOCK_STREAM) as s:
        s.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        try:
            s.bind((IP_ADDR, SERVER_PORT))
        except (gaierror, ConnectionRefusedError, OverflowError, OSError):
            print("Error while binding to the specified port")
            sys.exit()
        print(f"Starting the server on {IP_ADDR}:{SERVER_PORT}")
        try:
            port_manager = PortManager(SERVER_PORT, 2)
            s.listen()
            while True:
                print(f"Waiting for a connection")
                conn, addr = s.accept()
                conn.send(handle_new_connection().encode())
                conn.close()
        except KeyboardInterrupt:
            print("The server is shutting down.")
            sys.exit()
