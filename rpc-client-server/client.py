# Roman Soldatov
# B19-SD-01

# RPC Client for sending commands to a server
# Client can send, list, delete and get files
# Also, client can ask for result of math operations: *, /, -, +, >, <, >=, <=

import xmlrpc.client
import sys
from os.path import isfile
from socket import gaierror

CLIENT_DIRECTORY = "./client/"


def validate_command_line_input(argv):
    if len(argv) == 3:
        try:
            int(argv[2])
            return True
        except ValueError:
            pass
    return False


class Sender:
    def __init__(self, s):
        self.s = s
        self.input_command = ""
        self.operation = ""

    def _is_valid_operation(self):
        self.operation = self.input_command.split(" ")[0]
        args_num = len(self.input_command.split(" "))
        if self.operation == "send":
            return True if args_num == 2 else False
        elif self.operation == "list":
            return True if args_num == 1 else False
        elif self.operation == "delete":
            return True if args_num == 2 else False
        elif self.operation == "get":
            return True if (args_num == 2 or args_num == 3) else False
        elif self.operation == "calc":
            return True if args_num >= 2 else False
        return False

    def _send_command(self):
        file_path = self.input_command.split(" ")[1]
        filename = file_path.split("/")[-1]
        with open(file_path, 'rb') as file:
            file_binary = file.read()
            completed = self.s.send(filename, file_binary)
            if completed:
                print("Completed")
            else:
                print("Not completed\nFile already exists")

    def _list_command(self):
        for file in self.s.list():
            print(file)
        print("Completed")

    def _delete_command(self):
        filename = self.input_command.split(" ")[1]
        if self.s.delete(filename):
            print("Completed")
        else:
            print("Not completed\nNo such file")

    def _get_command(self):
        filename = self.input_command.split(" ")[1]
        new_filename = self.input_command.split(" ")[2] if len(self.input_command.split(" ")) == 3 else filename
        file_path = f"{CLIENT_DIRECTORY}{new_filename}"
        if isfile(file_path):
            print("Not completed\nFile already exists")
        else:
            data = self.s.get(filename)
            if not data:
                print("Not completed\nNo such file")
            else:
                with open(file_path, 'wb') as f:
                    f.write(data.data)
                    print("Completed")

    def _calc_command(self):
        expression = ' '.join(self.input_command.split(" ")[1:])
        success, result = self.s.calc(expression)
        if success:
            print(f"{result}\nCompleted")
        else:
            print(f"Not completed\n{result}")

    def send_command_server(self, input_command):
        self.input_command = input_command
        if self._is_valid_operation():
            if self.operation == "send":
                self._send_command()
            elif self.operation == "list":
                self._list_command()
            elif self.operation == "delete":
                self._delete_command()
            elif self.operation == "get":
                self._get_command()
            elif self.operation == "calc":
                self._calc_command()
        else:
            print("Not completed\nWrong command")


def start_client(server_ip_addr, server_port):
    try:
        with xmlrpc.client.ServerProxy(f'http://{server_ip_addr}:{server_port}') as s:
            sender = Sender(s)
            while True:
                print("\nEnter the command:")
                input_command = input("> ")
                if len(input_command.split(" ")) == 1 and input_command.split(" ")[0] == "quit":
                    print("Client is stopping")
                    break
                sender.send_command_server(input_command)
    except gaierror:
        print(f"Invalid IP address: {server_ip_addr}")
    except OverflowError:
        print(f"Port number must be 0-65535. Specified: {server_port}")
    except (ConnectionRefusedError, OSError):
        print("Server is not available")
    except KeyboardInterrupt:
        print("Client is stopping")


if __name__ == "__main__":
    if validate_command_line_input(sys.argv):
        start_client(sys.argv[1], int(sys.argv[2]))
    else:
        print("Usage example: python ./client.py <address> <port>")
