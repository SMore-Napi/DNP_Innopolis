# Roman Soldatov
# B19-SD-01

# Chord protocol. Stores Node class which implements the behavior of p2p node of Chord
# Available RPC commands: get_finger_table; quit

import time
import xmlrpc.client
import zlib
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


class Node(Thread):
    def __init__(self, node_ip_addr, node_port, ip_addr, registry_port):
        super().__init__()
        self.node_ip_addr = node_ip_addr
        self.node_port = node_port
        self.ip_addr = ip_addr
        self.registry_port = registry_port
        self.network_size = -1
        self.node_id = -1
        self.finger_table = {}
        self.pred_node = ()
        self.saved_files = []
        self.q = False
        self.updater = None

    def run(self):
        self.node_id, message = self._register_itself()
        if self.node_id == -1:
            print(message)
        else:
            try:
                self.network_size = int(message)
                time.sleep(1)
                self._update_finger_table(False)
                self.updater = Thread(target=self._update_finger_table, args=(True,))
                self.updater.start()
                self._start_node()
            except ValueError:
                print('Registry RPC message format error')

    def get_finger_table(self):
        """
        Return the finger table of the node which is just a dict of node ids and port numbers
        """
        return convert_dict_to_str(self.finger_table)

    def savefile(self, filename):
        succ = self._succ_id()
        hash_value = zlib.adler32(filename.encode())
        target_id = hash_value % self.network_size
        if self._is_between_neighbours(target_id, self.pred_node[0], self.node_id):
            if filename in self.saved_files:
                return False, f"{filename} already exists in node {self.node_id}"
            self.saved_files.append(filename)
            return True, f"{filename} is saved in node {self.node_id}"
        elif self._is_between_neighbours(target_id, self.node_id, succ):
            print(f"node {self.node_id} passed {filename} to node {succ}")
            return self._savefile_node(filename, self.finger_table[succ])
        else:
            farthest_node_id = self._find_farthest_node_node(target_id)
            print(f"node {self.node_id} passed {filename} to node {farthest_node_id}")
            return self._savefile_node(filename, self.finger_table[farthest_node_id])

    def getfile(self, filename):
        succ = self._succ_id()
        hash_value = zlib.adler32(filename.encode())
        target_id = hash_value % self.network_size
        if self._is_between_neighbours(target_id, self.pred_node[0], self.node_id):
            if filename in self.saved_files:
                return True, f"node {self.node_id} has {filename}"
            return False, f"node {self.node_id} doesn't have the {filename}"
        elif self._is_between_neighbours(target_id, self.node_id, succ):
            print(f"node {self.node_id} passed {filename} to node {succ}")
            return self._getfile_node(filename, self.finger_table[succ])
        else:
            farthest_node_id = self._find_farthest_node_node(target_id)
            print(f"node {self.node_id} passed {filename} to node {farthest_node_id}")
            return self._getfile_node(filename, self.finger_table[farthest_node_id])

    def set_predecessor(self, pred):
        self.pred_node = pred

    def add_data(self, data):
        self.saved_files += data

    def set_successor(self, succ):
        nodes_list = [succ]
        for node in self.finger_table.items():
            nodes_list.append(node)
        del nodes_list[-1]
        self.finger_table = {}
        for node in nodes_list:
            self.finger_table[node[0]] = node[1]

    def quit(self):
        """
        Quit the chord and then shut down
        """
        success, message = self._deregister_itself()
        if success:
            self.updater.do_run = False
            self._notify_succ()
            self._transfer_data()
            self._notify_pred()
            self.q = True
        return success, message

    def _register_itself(self):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{self.registry_port}') as registry:
                return registry.register(self.node_port)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.registry_port}")
        except (ConnectionRefusedError, OSError):
            print("Registry is not available")

    def _update_finger_table(self, infinite):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{self.registry_port}') as registry:
                if infinite:
                    while True:
                        table, self.pred_node = registry.populate_finger_table(self.node_id)
                        self.finger_table = convert_dict_to_int(table)
                        time.sleep(1)
                else:
                    table, self.pred_node = registry.populate_finger_table(self.node_id)
                    self.finger_table = convert_dict_to_int(table)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.registry_port}")
        except (ConnectionRefusedError, OSError):
            print("Registry is not available")

    def _start_node(self):
        try:
            with SimpleXMLRPCServer((self.node_ip_addr, self.node_port), logRequests=False, allow_none=True) as node:
                node.register_introspection_functions()
                node.register_function(self.get_finger_table, 'get_finger_table')
                node.register_function(self.savefile, 'savefile')
                node.register_function(self.getfile, 'getfile')
                node.register_function(self.set_predecessor, 'set_predecessor')
                node.register_function(self.add_data, 'add_data')
                node.register_function(self.getfile, 'getfile')
                node.register_function(self.set_successor, 'set_successor')
                node.register_function(self.quit, 'quit')
                while not self.q:
                    node.handle_request()
        except (gaierror, OSError):
            print(f"Invalid IP address: {self.node_ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.node_port}")

    def _deregister_itself(self):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{self.registry_port}') as registry:
                return registry.deregister(self.node_id)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {self.registry_port}")
        except (ConnectionRefusedError, OSError):
            print("Registry is not available")

    def _savefile_node(self, filename, node_port):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{node_port}') as node:
                return node.savefile(filename)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {node_port}")
        except (ConnectionRefusedError, OSError):
            for node_id in self.finger_table:
                if self.finger_table[node_id] == node_port:
                    print(f"Node {node_id}:{node_port} is not available")
                    break

    def _getfile_node(self, filename, node_port):
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{node_port}') as node:
                return node.getfile(filename)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {node_port}")
        except (ConnectionRefusedError, OSError):
            for node_id in self.finger_table:
                if self.finger_table[node_id] == node_port:
                    print(f"Node {node_id}:{node_port} is not available")
                    break

    def _notify_succ(self):
        succ_id = self._succ_id()
        succ_port = self.finger_table[succ_id]
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{succ_port}') as node:
                node.set_predecessor(self.pred_node)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {succ_port}")
        except (ConnectionRefusedError, OSError):
            print(f"Node {succ_id}:{succ_port} is not available")

    def _transfer_data(self):
        succ_id = self._succ_id()
        succ_port = self.finger_table[succ_id]
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{succ_port}') as node:
                node.add_data(self.saved_files)
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {succ_port}")
        except (ConnectionRefusedError, OSError):
            print(f"Node {succ_id}:{succ_port} is not available")

    def _notify_pred(self):
        succ_id = self._succ_id()
        succ_port = self.finger_table[succ_id]
        try:
            with xmlrpc.client.ServerProxy(f'http://{self.ip_addr}:{succ_port}') as node:
                node.set_successor((succ_id, succ_port))
        except gaierror:
            print(f"Invalid IP address: {self.ip_addr}")
        except OverflowError:
            print(f"Port number must be 0-65535. Specified: {succ_port}")
        except (ConnectionRefusedError, OSError):
            print(f"Node {succ_id}:{succ_port} is not available")

    def _succ_id(self):
        return next(iter(self.finger_table))

    def _is_between_neighbours(self, target_id, l_id, r_id):
        if l_id < target_id <= r_id:
            return True
        if l_id > r_id:
            if l_id < target_id < self.network_size:
                return True
            if 0 <= target_id <= r_id:
                return True
        return False

    def _find_farthest_node_node(self, target_id):
        nodes_id = sorted(self.finger_table.keys())
        if target_id < nodes_id[0]:
            return nodes_id[-1]
        nodes_id.reverse()
        for i in nodes_id:
            if target_id >= i:
                return i
