# Roman Soldatov
# B19-SD-01

# Chord protocol. Implements the user interface
# main.py accepts three arguments: m, first_port, and last_port.
# Firstly, it creates the Registry and then nodes.
# Available commands: get_chord_info; get_finger_table; quit

import sys
import xmlrpc.client
import zlib
from socket import gaierror

from node import Node
from registry import Registry


def is_valid_command_line_input(argv):
    if len(argv) == 3:
        try:
            if int(argv[1]) <= int(argv[2]):
                return True
        except ValueError:
            pass
    if len(argv) == 4:
        try:
            int(argv[1])
            if int(argv[2]) <= int(argv[3]):
                return True
        except ValueError:
            pass
    return False


def get_input_arguments(argv):
    if len(argv) == 3:
        return 5, int(argv[1]), int(argv[2])
    if len(argv) == 4:
        return int(argv[1]), int(argv[2]), int(argv[3])


def convert_dict_to_int(dictionary):
    converted_dict = {}
    for key in dictionary.keys():
        converted_dict[int(key)] = dictionary[key]
    return converted_dict


def get_chord_info(ip_address, p_registry):
    try:
        with xmlrpc.client.ServerProxy(f'http://{ip_address}:{p_registry}') as registry:
            print(convert_dict_to_int(registry.get_chord_info()))
    except gaierror:
        print(f"Invalid IP address: {ip_address}")
    except OverflowError:
        print(f"Port number must be 0-65535. Specified: {p_registry}")
    except (ConnectionRefusedError, OSError):
        print("Registry is not available")
    except KeyboardInterrupt:
        print("Main is stopping")


def get_finger_table(ip_address, p):
    try:
        with xmlrpc.client.ServerProxy(f'http://{ip_address}:{p}') as node:
            print(convert_dict_to_int(node.get_finger_table()))
    except gaierror:
        print(f"Invalid IP address: {ip_address}")
    except OverflowError:
        print(f"Port number must be 0-65535. Specified: {p}")
    except (ConnectionRefusedError, OSError):
        print("Node is not available")
    except KeyboardInterrupt:
        print("Main is stopping")


def savefile(ip_address, p, filename, m):
    try:
        with xmlrpc.client.ServerProxy(f'http://{ip_address}:{p}') as node:
            hash_value = zlib.adler32(filename.encode())
            target_id = hash_value % 2 ** m
            print(f'{filename} has identifier {target_id}')
            print(node.savefile(filename))
    except gaierror:
        print(f"Invalid IP address: {ip_address}")
    except OverflowError:
        print(f"Port number must be 0-65535. Specified: {p}")
    except (ConnectionRefusedError, OSError):
        print("Node is not available")
    except KeyboardInterrupt:
        print("Main is stopping")


def getfile(ip_address, p, filename, m):
    try:
        with xmlrpc.client.ServerProxy(f'http://{ip_address}:{p}') as node:
            hash_value = zlib.adler32(filename.encode())
            target_id = hash_value % 2 ** m
            print(f'{filename} has identifier {target_id}')
            print(node.getfile(filename))
    except gaierror:
        print(f"Invalid IP address: {ip_address}")
    except OverflowError:
        print(f"Port number must be 0-65535. Specified: {p}")
    except (ConnectionRefusedError, OSError):
        print("Node is not available")
    except KeyboardInterrupt:
        print("Main is stopping")


def quit_node(ip_address, p, port_numbers):
    if p not in port_numbers:
        print(f"Node with port {p} isn’t part of the network")
    else:
        try:
            with xmlrpc.client.ServerProxy(f'http://{ip_address}:{p}') as node:
                print(node.quit())
        except gaierror:
            print(f"Invalid IP address: {ip_address}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {p}")
        except (ConnectionRefusedError, OSError):
            print("Node is not available")
        except KeyboardInterrupt:
            print("Main is stopping")


def handle_input(ip_address, p_registry, input_command, m, port_numbers):
    if input_command == "get_chord_info":
        get_chord_info(ip_address, p_registry)
    else:
        input_command = input_command.split(" ")
        if len(input_command) == 2:
            try:
                p = int(input_command[1])
                if input_command[0] == "get_finger_table":
                    get_finger_table(ip_address, p)
                elif input_command[0] == "quit":
                    quit_node(ip_address, p, port_numbers)
            except ValueError:
                pass
        elif len(input_command) == 3:
            try:
                p = int(input_command[1])
                filename = input_command[2]
                if input_command[0] == "save":
                    savefile(ip_address, p, filename, m)
                elif input_command[0] == "get":
                    getfile(ip_address, p, filename, m)
            except ValueError:
                pass


def accept_command(ip_address, p_registry, m, port_numbers):
    try:
        while True:
            input_command = input("> ")
            handle_input(ip_address, p_registry, input_command, m, port_numbers)
    except KeyboardInterrupt:
        print("Stopping")


def create_registry_nodes(m, ip_address, p_registry, p_nodes):
    Registry(m, ip_address, p_registry).start()
    nodes = [Node(ip_address, node_port, ip_address, p_registry) for node_port in p_nodes]
    for node in nodes:
        node.start()
    print(f"Registry and {len(p_nodes)} nodes are created.")


if __name__ == "__main__":
    if is_valid_command_line_input(sys.argv):
        ip = '127.0.0.1'
        length_identifiers, first_port, last_port = get_input_arguments(sys.argv)
        registry_port = first_port - 1
        port_numbers = list(range(first_port, last_port + 1))
        create_registry_nodes(length_identifiers, ip, registry_port, port_numbers)
        accept_command(ip, registry_port, length_identifiers, port_numbers)
    else:
        print("Usage example: python ./main.py <m> <first_port> <last_port>")
