# Roman Soldatov
# B19-SD-01

# RPC Server for storing files and performing simple calculator operations
# Server allows to multiple clients to send, list, delete and get files.
# Also, server can perform math operations: *, /, -, +, >, <, >=, <=


from socket import gaierror
from xmlrpc.server import SimpleXMLRPCServer
import sys
from os.path import isfile, join, exists
from os import listdir, remove, makedirs

SERVER_DIRECTORY = "./server/"


def is_valid_command_line_input(argv):
    if len(argv) == 3:
        try:
            int(argv[2])
            return True
        except ValueError:
            pass
    return False


def check_server_dir():
    if not exists(SERVER_DIRECTORY):
        makedirs(SERVER_DIRECTORY)


class Calculator:
    def __init__(self, expression):
        self._expression = expression
        self.result = (False, "Wrong expression") if not self._is_valid_expression() else self._calc_result()

    def _is_valid_expression(self):
        command = self._expression.split(" ")
        if len(command) != 3:
            return False
        self._operator, self._left, self._right = command
        if self._operator not in ["*", "/", "-", "+", ">", "<", ">=", "<="]:
            return False
        try:
            float(self._left)
            float(self._right)
        except ValueError:
            return False
        return True

    def _convert_to_number(self, operand):
        return float(operand) if '.' in operand else int(operand)

    def _perform_operation(self):
        if self._operator == "*":
            return True, self._left * self._right
        if self._operator == "/":
            try:
                return True, self._left / self._right
            except ZeroDivisionError:
                return False, "Division by zero"
        if self._operator == "-":
            return True, self._left - self._right
        if self._operator == "+":
            return True, self._left + self._right
        if self._operator == ">":
            return True, self._left > self._right
        if self._operator == "<":
            return True, self._left < self._right
        if self._operator == ">=":
            return True, self._left >= self._right
        if self._operator == "<=":
            return True, self._left <= self._right

    def _calc_result(self):
        self._left = self._convert_to_number(self._left)
        self._right = self._convert_to_number(self._right)
        return self._perform_operation()


def send_file(filename, data):
    check_server_dir()
    file_path = f"{SERVER_DIRECTORY}{filename}"
    if isfile(file_path):
        print(f"{filename} not saved")
        return False
    with open(file_path, 'wb') as f:
        f.write(data.data)
        print(f"{filename} saved")
        return True


def list_files():
    check_server_dir()
    return [f for f in listdir(SERVER_DIRECTORY) if isfile(join(SERVER_DIRECTORY, f))]


def delete_file(filename):
    check_server_dir()
    file_path = f"{SERVER_DIRECTORY}{filename}"
    if isfile(file_path):
        remove(file_path)
        print(f"{filename} deleted")
        return True
    print(f"{filename} not deleted")
    return False


def get_file(filename):
    check_server_dir()
    file_path = f"{SERVER_DIRECTORY}{filename}"
    if not isfile(file_path):
        print(f"No such file: {filename}")
        return False
    with open(file_path, 'rb') as file:
        print(f"File send: {filename}")
        return file.read()


def calculate(expression):
    calculator = Calculator(expression)
    if calculator.result[0]:
        print(f"{expression} -- done")
    else:
        print(f"{expression} -- not done")
    return calculator.result


def start_server(ip_addr, port):
    try:
        with SimpleXMLRPCServer((ip_addr, port), logRequests=False) as server:
            server.register_introspection_functions()
            server.register_function(send_file, 'send')
            server.register_function(list_files, 'list')
            server.register_function(delete_file, 'delete')
            server.register_function(get_file, 'get')
            server.register_function(calculate, 'calc')
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                print("Server is stopping")
    except (gaierror, OSError):
        print(f"Invalid IP address: {ip_addr}")
    except OverflowError:
        print(f"Port number must be 0-65535. Specified: {port}")


if __name__ == "__main__":
    if is_valid_command_line_input(sys.argv):
        start_server(sys.argv[1], int(sys.argv[2]))
    else:
        print("Usage example: python ./server.py <address> <port>")
