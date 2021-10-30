# Roman Soldatov
# B19-SD-01

import xmlrpc.client
from socket import gaierror


class Client:
    def __init__(self):
        print("The client starts")
        self.server_ip = ""
        self.server_port = -1

    def start_client(self):
        try:
            while True:
                try:
                    input_command = input("> ").split(" ")
                    if len(input_command) == 1:
                        if input_command[0] == "getleader":
                            self._get_leader()
                        elif input_command[0] == "quit":
                            print("The client ends")
                            break
                    elif len(input_command) == 2:
                        if input_command[0] == "suspend":
                            self._suspend(int(input_command[1]))
                    elif len(input_command) == 3:
                        if input_command[0] == "connect":
                            self._connect(input_command[1], int(input_command[2]))
                except ValueError:
                    pass
        except KeyboardInterrupt:
            print("The client ends")

    def _connect(self, address, port):
        self.server_ip = address
        self.server_port = port

    def _get_leader(self):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.server_ip}:{self.server_port}') as s:
                print(s.get_leader())
        except gaierror:
            print(f"Invalid IP address: {self.server_ip}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.server_port}")
        except (ConnectionRefusedError, OSError):
            print(f"The server <{self.server_ip}>:<{self.server_port}> is unavailable.")

    def _suspend(self, period):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.server_ip}:{self.server_port}') as s:
                s.suspend(period)
        except gaierror:
            print(f"Invalid IP address: {self.server_ip}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.server_port}")
        except (ConnectionRefusedError, OSError):
            print(f"The server <{self.server_ip}>:<{self.server_port}> is unavailable.")


if __name__ == "__main__":
    Client().start_client()
