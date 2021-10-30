# Roman Soldatov
# B19-SD-01

import sys
from socket import gaierror
from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import random
import time
import datetime
from enum import Enum
from threading import Thread


class State(Enum):
    Follower = 1
    Candidate = 2
    Leader = 3


def read_config_file(input_id):
    s_dic = {}
    s_ip = ""
    s_p = -1
    for line in open('config.conf', 'r').readlines():
        line_id, line_ip, line_port = line.split(" ")
        if line_id == input_id:
            s_ip, s_p = line_ip, int(line_port)
        else:
            s_dic[int(line_id)] = (line_ip, int(line_port))
    return int(input_id), s_ip, s_p, s_dic


def generate_time():
    return random.randrange(150, 301) * 0.001


class Server:
    def __init__(self, input_id):
        self.sleep = False
        self.state = State.Follower
        self.leader_id = -1
        self.term_number = 0
        self.voted = False
        self.number_votes = 0
        self.timer = generate_time()
        self.restart_timer = False
        self.server_id, self.server_ip, self.server_port, self.servers_dic = read_config_file(input_id)
        self.server_t = Thread(target=self._accept_requests)
        self.timer_t = Thread(target=self._wait_for)
        self.leadership_t = Thread(target=self._remain_leadership)

    def start_server(self):
        print(f"Server is started at {self.server_ip}:{self.server_port}")
        self._print_state()
        self.server_t.start()
        self.leadership_t.start()
        self.timer_t.start()

    def request_vote(self, term, candidate_id):
        if not self.sleep:
            self.restart_timer = True
            if term > self.term_number:
                self.term_number = term
                self.voted = False
            if self.term_number == term and not self.voted:
                self.voted = True
                self.state = State.Follower
                self.leader_id = candidate_id
                print(f"Voted for node {candidate_id}")
                return self.term_number, True
            return self.term_number, False

    def append_entries(self, term, leader_id):
        if not self.sleep:
            self.restart_timer = True
            if term >= self.term_number:
                updated_state = True if term > self.term_number else False
                self.leader_id = leader_id
                self.term_number = term
                self.state = State.Follower
                if updated_state:
                    self._print_state()
                return True
            return False

    def get_leader(self):
        if not self.sleep:
            print("Command from client: getleader")
            result = f"{self.server_id} {self.server_ip} {self.server_port}" \
                if self.state == State.Leader \
                else f"{self.leader_id} {self.servers_dic[self.leader_id][0]} {self.servers_dic[self.leader_id][1]}"
            print(result)
            return result

    def suspend(self, period):
        if not self.sleep:
            print(f"Command from client: suspend {period}")
            print(f"Sleeping for {period} seconds")
            self.sleep = True
            time.sleep(period)
            self.sleep = False

    def _accept_requests(self):
        if not self.sleep:
            try:
                with SimpleXMLRPCServer((self.server_ip, self.server_port), logRequests=False,
                                        allow_none=True) as server:
                    server.register_introspection_functions()
                    server.register_function(self.request_vote, 'request_vote')
                    server.register_function(self.append_entries, 'append_entries')
                    server.register_function(self.get_leader, 'get_leader')
                    server.register_function(self.suspend, 'suspend')
                    try:
                        server.serve_forever()
                    except KeyboardInterrupt:
                        print("Server is stopping")
            except (gaierror, OSError):
                print(f"Invalid IP address: {self.server_ip}")
            except OverflowError:
                print(f"Port number must be 0-65535. Specified: {self.server_port}")

    def _remain_leadership(self):
        while True:
            if not self.sleep:
                if self.state == State.Leader:
                    threads = []
                    for node in self.servers_dic:
                        node_ip, node_port = self.servers_dic[node]
                        threads.append(Thread(target=self._send_heartbeat_message, args=(node_ip, node_port,)))
                    [t.start() for t in threads]
                    [t.join() for t in threads]
                    time.sleep(0.05)

    def _wait_for(self):
        start_time = datetime.datetime.now()
        while True:
            if self.restart_timer:
                self.restart_timer = False
                start_time = datetime.datetime.now()
            elif (datetime.datetime.now() - start_time).total_seconds() > self.timer:
                if self.state == State.Follower:
                    self._start_election_process()
                elif self.state == State.Candidate:
                    if self.number_votes >= len(self.servers_dic.keys()) / 2:
                        self.restart_timer = True
                        self.state = State.Leader
                        self._print_state()
                    else:
                        self.timer = generate_time()
                        self.state = State.Follower
                        self._print_state()
                elif self.state == State.Leader:
                    self.restart_timer = True

    def _send_heartbeat_message(self, s_ip, s_port):
        if not self.sleep:
            if self.state == State.Leader:
                try:
                    with xmlrpc.client.ServerProxy(f'http://{s_ip}:{s_port}') as s:
                        success = s.append_entries(self.term_number, self.server_id)
                        if not success:
                            self.state = State.Follower
                            self._print_state()
                except gaierror:
                    print(f"Invalid IP address: {s_ip}")
                except OverflowError:
                    print(f"Port number must be 0-65535. Specified: {s_port}")
                except (ConnectionRefusedError, OSError):
                    pass
                    # print(f"The server <{s_ip}>:<{s_port}> is unavailable.")

    def _ask_for_vote(self, s_ip, s_port):
        if not self.sleep:
            if self.state == State.Candidate:
                try:
                    with xmlrpc.client.ServerProxy(f'http://{s_ip}:{s_port}') as s:
                        term, voted = s.request_vote(self.term_number, self.server_id)
                        if voted:
                            self.number_votes += 1
                        if term > self.term_number:
                            self.state = State.Follower
                            self.term_number = term
                            self._print_state()
                except gaierror:
                    print(f"Invalid IP address: {s_ip}")
                except OverflowError:
                    print(f"Port number must be 0-65535. Specified: {s_port}")
                except (ConnectionRefusedError, OSError):
                    pass
                    # print(f"The server <{s_ip}>:<{s_port}> is unavailable.")

    def _start_election_process(self):
        if not self.sleep:
            self.state = State.Candidate
            print("The leader is dead")
            self._print_state()
            self.term_number += 1
            self.number_votes = 1
            self.request_vote(self.term_number, self.server_id)
            # print(f"Voted for node {self.server_id}")
            # self.number_votes = 1
            # self.restart_timer = True
            threads = []
            for node in self.servers_dic:
                node_ip, node_port = self.servers_dic[node]
                threads.append(Thread(target=self._ask_for_vote, args=(node_ip, node_port,)))
            [t.start() for t in threads]
            [t.join() for t in threads]
            print("Votes received")
            if self.state == State.Candidate and self.number_votes >= len(self.servers_dic.keys()) / 2:
                self.restart_timer = True
                self.state = State.Leader
                self._print_state()

    def _reset_time(self):
        self.timer_t = Thread(target=self._wait_for)
        self.timer_t.start()

    def _print_state(self):
        status = ""
        if self.state == State.Follower:
            status = "follower"
        if self.state == State.Candidate:
            status = "candidate"
        if self.state == State.Leader:
            status = "leader"
        print(f"I am a {status}. Term: {self.term_number}")


if __name__ == "__main__":
    Server(sys.argv[1]).start_server()
