# Roman Soldatov
# B19-SD-01

# Chord protocol. Stores Registry class which Implements the behavior of Registry node.
# Available RPC commands: register; deregister; deregister; get_chord_info; populate_finger_table

import random
from socket import gaierror
from threading import Thread
from xmlrpc.server import SimpleXMLRPCServer


def convert_dict_to_str(dictionary):
    converted_dict = {}
    for key in dictionary.keys():
        converted_dict[str(key)] = dictionary[key]
    return converted_dict


def convert_dict_to_int(dictionary):
    converted_dict = {}
    for key in dictionary.keys():
        converted_dict[int(key)] = dictionary[key]
    return converted_dict


class Registry(Thread):
    def __init__(self, m, ip_addr, registry_port):
        super().__init__()
        self.id_port_dict = {}
        self.m = m
        self.ip_addr = ip_addr
        self.registry_port = registry_port
        self.max_size = 2 ** m
        self.identifier_space = list(range(0, self.max_size))

    def run(self):
        try:
            with SimpleXMLRPCServer((self.ip_addr, self.registry_port), logRequests=False) as server:
                server.register_introspection_functions()
                server.register_function(self.register, 'register')
                server.register_function(self.deregister, 'deregister')
                server.register_function(self.get_chord_info, 'get_chord_info')
                server.register_function(self.populate_finger_table, 'populate_finger_table')
                try:
                    server.serve_forever()
                except KeyboardInterrupt:
                    print("Registry is stopping")
        except (gaierror, OSError):
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.registry_port}")

    def register(self, port):
        """
        Can be invoked by new node to register itself
        """
        random.seed(0)
        if len(self.id_port_dict) == self.max_size:
            return -1, 'the Chord is full'
        while True:
            new_id = random.randrange(len(self.identifier_space))
            if new_id not in self.id_port_dict:
                self.id_port_dict[new_id] = port
                return new_id, self.max_size

    def deregister(self, node_id):
        """
        Can be invoked by the registered node to deregister itself
        """
        try:
            port = self.id_port_dict.pop(node_id)
            return True, f'Node {node_id} with port {port} was deregistered'
        except KeyError:
            return False, 'No such id exists'

    def get_chord_info(self):
        """
        Can be invoked by the main program to get the information about chord: dict of node id and port numbers
        """
        return convert_dict_to_str(self.id_port_dict)

    def populate_finger_table(self, node_id):
        """
        Generate the dict of the ids and port numbers that the requesting node can communicate
        """
        finger_table = {}
        for i in range(1, self.m + 1):
            n_id = self._succ((node_id + 2 ** (i - 1)) % self.max_size)
            finger_table[n_id] = self.id_port_dict[n_id]
        pred_node_id = self._pred(node_id)
        return convert_dict_to_str(finger_table), (pred_node_id, self.id_port_dict[pred_node_id])

    def _succ(self, node_id):
        for next_node_id in sorted(self.id_port_dict.keys()):
            if node_id <= next_node_id:
                return next_node_id

    def _pred(self, node_id):
        nodes = sorted(self.id_port_dict.keys())
        nodes.reverse()
        for prev_node_id in nodes:
            if node_id > prev_node_id:
                return prev_node_id
        return nodes[0]
