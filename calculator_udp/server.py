# Roman Soldatov
# B19-SD-01

# Server for UDP calculator

from socket import socket, AF_INET, SOCK_DGRAM

IP_ADDR = "127.0.0.1"
PORT = 65432
BUF_SIZE = 100000


class ArgsException(Exception):
    pass


def convert_to_number(operand):
    if '.' in operand:
        return float(operand)
    return int(operand)


def perform_operation(operator, left_operand, right_operand):
    """Return the operation result"""
    if operator == "*":
        return left_operand * right_operand
    if operator == "/":
        try:
            return left_operand / right_operand
        except ZeroDivisionError:
            return "division by zero"
    if operator == "-":
        return left_operand - right_operand
    if operator == "+":
        return left_operand + right_operand
    if operator == ">":
        return left_operand > right_operand
    if operator == "<":
        return left_operand < right_operand
    if operator == ">=":
        return left_operand >= right_operand
    if operator == "<=":
        return left_operand <= right_operand


def get_result(input_data):
    # Arguments validation
    try:
        command = input_data.split(" ")
        if len(command) != 3:
            raise ArgsException("Arguments are not in the proper format: operator left_operand right_operand")
        operator, left_operand, right_operand = command
        # Operator validation
        if not (operator in ["*", "/", "-", "+", ">", "<", ">=", "<="]):
            raise ArgsException("No such operator found: " + operator)
    except ArgsException as e:
        return e.args[0]

    # Operands validation
    try:
        float(left_operand)
    except ValueError:
        return left_operand + " is not operand!"
    try:
        float(right_operand)
    except ValueError:
        return right_operand + " is not operand!"

    # Determine the type of operands and correctly convert the type
    left_operand = convert_to_number(left_operand)
    right_operand = convert_to_number(right_operand)

    # Perform the operation
    return perform_operation(operator, left_operand, right_operand)


with socket(AF_INET, SOCK_DGRAM) as s:
    s.bind((IP_ADDR, PORT))
    print("Waiting for a new request")
    try:
        while True:
            data, addr = s.recvfrom(BUF_SIZE)
            request = data.decode()
            print(f"Request by {addr}: {request}")
            result = str(get_result(request))
            print(f"Result: {result}\n")
            s.sendto(result.encode(), addr)
    except KeyboardInterrupt:
        print("Keyboard interrupt, server is shutting down.")
