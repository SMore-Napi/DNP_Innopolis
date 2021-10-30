# DNP Innopolis
Lab tasks of F21 **Distributed and Network Programming** course.

> Semester 5, 3rd study-year, Innopolis University.

## Sequential vs Parallel processing
Compare the performance of sequential and parallel processing by finding whether the given numbers are prime or not using Python's `multiprocessing` package.

Check it here: [Sequential vs Parallel processing](/sequential-vs-parallel-processing)

## A client-server calculator app with UDP sockets
* Client
    - interactively accepts calculation command from user input in following format:
    `operator left_operand right_operand`
    - sends the command to the server and receives the response from it
    - handles **KeyboardInterrupt** or entering *“quit”* / *“Quit”* / *“QUIT”* commands to shut down.
* Server
    - accepts commands in following format:
    `operator left_operand right_operand`
    - determines the type of the operation to perform `*, /, -, +, >, <, >=, <=`
    - determines the type of operands and correctly convert the type: *int or float*
    - performs calculation and returns the result to the client

Check it here: [Calculator UDP](/calculator_udp)

## Reliable file transfer on top of UDP
* Client
    - provide the file name as an argument in the command line.
    - sends **start** message: `s | seqno0 | extension | size`
        - `s` indicates that it is a **start** message
        - `|` is a delimiter that divides the neighbouring parts in the message
        - `seqno0` indicates the start sequence number for messages of this file transfer session
        - `extension` is the extension of the file that will be transferred, e.g., jpg, txt, doc, py, etc.
        - `size` is the size of the file being transferred.
    - send **data** message: `d | seqno | data_bytes`
        - `d` indicates that it is a data message
        - `seqno` is the seqno of this data message
        - `data_bytes` is the part of the file being transmitted
* Server
    - If the server receives the start message, it replies with an ack message which has the following format: `a | next_seqno | maxsize`
        - `a` indicates that it is an **ack** message
        - `next_seqno` is the sequence number (`seqno`) of the next message the server is waiting to receive.
        - `maxsize` indicates the maximum size for the message, i.e., the UDP buffer size at the server.
    - If the server receives the data message, it replies with an ack message which has the following format: `a | next_seqno`
        - `a` indicates that it is an **ack** message
        - `next_seqno` is the sequence number (`seqno`) of the next message the server is waiting to receive.
    - The server ignores the duplicate messages received from the same client.
    - If the client isn’t active for very long (more than 3s) and the associated file reception session isn’t yet finished, then the server abandons this session and removes everything related to this station.
    - The server holds the information related to the successfully finished file reception for some time (1.0s) before finally removing it.

Check it here: [File transfer UDP](/file_transfer_udp)

## TCP Client-Server number guessing game
> 1. The game is a simple number guessing game.
> 2. The user specifies the range of numbers.
> 3. The game generates a random number in this range.
> 4. The user has 5 attempts to guess the number.
> 5. On each user's input game responds with a message (*"Greater"* / *"Less"*)
> 6. When the user guesses the right number or the number of attempts is exceeded, the game responds with *"You win!"* or *"You lose"* message respectively and the game ends.

* Client
    - Client application has two command-line arguments: `server ip address` and `server port`.
    - At the start, a client connects to the server on the provided address and port using a TCP socket.
    - After connecting to the server, the client waits for the server's response with the new port number, and the connection is closed by the server.
    - Client connects to a new port of the server and the game starts.
* Server
    - Server application can serve up to **two** clients at the same time.
    - Server application has one command-line argument: `server port`.
    - When the server accepts an incoming connection from a client it creates a new **thread** in which the game logic will run.
    - If there is no room for a new client, the server sends a message to the client *"The server is full"* and closes the connection.

Check it here: [TCP Client-Server number guessing game](/tcp-client-server-number-guessing-game)

## RPC client-server
Both server and client use **Remote Procedure Call** (RPC) from python's `xmlrpc` module.

* Client
    - Has 2 command-line arguments: `ip address` and `port` of the server`.
    - Interactively gets operations from the user.
    - At the end of each operation prints either **Completed** or **Not completed** message.
* Server
    - Has 2 command-line arguments: `ip address` and `port`.
    - Always ready to receive connections from clients.

**Operations**
- `send <filename>` - sends specified file to the server.
- `list` - prints all the files saved on the server.
- `delete <filename>` - deletes saved file from server.
- `get <filename> <new filename>` - downloads the file `filename` from the server and saves it with the same name if the `new filename` is
not specified, or with the `new filename` otherwise.
- `calc <expression>` - expression has the format: `operator left right`

Check it here: [RPC client-server](/rpc-client-server)

## Chord protocol
* `main.py` - implements the user interface.
* `node.py` - stores **Node** class which implements the behavior of p2p node of Chord.
    - `get_finger_table()` - returns the finger table of the node which is just a **dict** of node **ids** and **port** numbers.
    - `savefile(filename)` - calculates the hash of the given filename and then the id where this filename should be stored using the `lookup(target_id)` procedure of chord protocol.
    - `getfile(filename)` - calculates the **target_id** and finds the successor of it using the **finger_table**.
    - `quit()` - calls the `deregister(id)` method of **Registry** to quit the chord and then shut down the **Node**.
* `registry.py` - stores **Registry** class which Implements the behaviour of Registry node.
    - `register(port)` - method can be invoked by new node to register itself.
    - `deregister(id)` - method can be invoked by the registered node to deregister itself.
    - `get_chord_info()` - method is invoked by the `main` program to get the information about chord: **dict** of node **ids** and **port** numbers.
    - `populate_finger_table(id)` - method is responsible to generate the **dict** of the **(id, port number)** pairs that the requesting node can directly communicate with.

Check it here: [Chord protocol](/chord-protocol)

## RAFT Protocol (Leader election)
* Client
    - `connect <address> <port>` - sets the server address and port to the specified ones. It does not connect anywhere, but `getleader` and `suspend` commands will be now sent to this address.
    - `getleader` - requests the current Leader's id and the address from the server. 
    - `suspend <period>` - makes the server to sleep for `<period>` seconds.
    - `quit` - exits the program.
* Configuration file
    - Contains information about the system in the format: `id address port`. 
    - The number of lines means the number of servers (nodes) in the system.
    - Has the name `config.conf`.
* Server
    - Server has one command line argument: `id`.
    - At the start, server reads the config file, finds the corresponding address and the port number, and binds to it.
    - States
        - **Follower** - the initial state of the server.
        - **Candidate** - trying to become a leader.
        - **Leader** - runs the system. Every **50 milliseconds** sends an `AppendEntries` request to all other servers.
    - Functions
        - `RequestVote(term, candidateId)` - is called by the **Candidate** during the elections to collect votes.
        - `AppendEntries(term, leaderId)` - In this implementation, this function is only used to send heartbeat messages.
        - `GetLeader()` - returns the current Leader id and address.
        - `Suspend(period)` - makes the server sleep for `period` seconds. This function is called by the client.

Check it here: [RAFT Protocol (Leader election)](/raft-protocol)