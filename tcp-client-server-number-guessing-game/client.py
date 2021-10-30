# Roman Soldatov
# B19-SD-01

# Client for the TCP number guessing game.
# Client connects to the server and receives new port number
# Client connects to a new port of the server and the game starts

from socket import socket, AF_INET, SOCK_STREAM, gaierror, error
import sys

DEST_IP_ADDR = '127.0.0.1'
BUF_SIZE = 1024

protocol_format = {
    "finish": {
        "full": "The server is full",
        "win": "You win!",
        "lose": "You lose"
    },
    "gr": "Greater",
    "le": "Less",
    "welcome": "Welcome to the number guessing game!"
}


def validate_command_line_input():
    if len(sys.argv) == 3:
        try:
            int(sys.argv[2])
            return
        except ValueError:
            pass
    print("Usage example: python ./client.py <address> <port>")
    sys.exit()


def input_range():
    """
    Validate if a user input two integer numbers. The second one is greater
    """
    while True:
        print("Enter the range:")
        message = input()
        if len(message.split(" ")) == 2:
            min_number, max_number = message.split(" ")
            try:
                if int(min_number) < int(max_number):
                    return message
            except ValueError:
                pass


def input_integer():
    """
    Validate if a user input an integer number
    """
    while True:
        message = input()
        try:
            int(message)
            return message
        except ValueError:
            pass


def validate_received_message_game(message):
    """
    Validate if the received message during the game is correct according to the protocol
    """
    try:
        code, data = message.split("|")
        if code not in ["finish", "gr", "le", "a", "welcome"]:
            return False
        if code == "finish" and data not in ["win", "lose"]:
            return False
        if code in ["gr", "le", "a"]:
            int(data)
        return True
    except ValueError:
        return False


def get_game_port(server_ip, server_port):
    """
    Connecting to the server and receive a message with the port number
    to reconnect for the game
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            s.connect((server_ip, server_port))
            code, data = s.recv(BUF_SIZE).decode().split("|")
            if code == "finish" and data == "full":
                print(protocol_format[code][data])
                sys.exit()
            elif code == "port":
                try:
                    return int(data)
                except ValueError:
                    pass
            print("The server sent undefined message.")
            sys.exit()
        except (gaierror, ConnectionRefusedError, ConnectionResetError, OverflowError):
            print("Server is unavailable")
            sys.exit()


def start_game(server_ip, server_port):
    """
    Connecting to the server and playing the guess number game
    """
    with socket(AF_INET, SOCK_STREAM) as s:
        try:
            s.connect((server_ip, server_port))
            try:
                while True:
                    message = s.recv(BUF_SIZE).decode()
                    if not validate_received_message_game(message):
                        print(message)
                        print("Connection lost")
                        sys.exit()
                    code, data = message.split("|")
                    if code == "finish" and data in ["win", "lose"]:
                        print(protocol_format[code][data])
                        break
                    if code == "welcome":
                        print(protocol_format[code])
                        s.send(input_range().encode())
                    elif code in ["gr", "le", "a"]:
                        if code in ["gr", "le"]:
                            print(protocol_format[code])
                        print(f"You have {data} attempts")
                        s.send(input_integer().encode())
            except KeyboardInterrupt:
                print("Client shutting down")
                sys.exit()
        except (gaierror, ConnectionRefusedError, ConnectionResetError, OverflowError):
            print("Connection lost")


if __name__ == "__main__":
    validate_command_line_input()
    DEST_IP_ADDR = sys.argv[1]
    SERVER_PORT = int(sys.argv[2])
    GAME_PORT = get_game_port(DEST_IP_ADDR, SERVER_PORT)
    start_game(DEST_IP_ADDR, GAME_PORT)
