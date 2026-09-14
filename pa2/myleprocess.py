import sys
import uuid
import json
import socket
import threading
import queue
import logging
import os

ROOT_PATH = "/home/harshpanchal/Coding/python/cs158a/pa1/"

BUFFER_SIZE = 1024

class Message:
    def __init__(self, uuid: uuid.UUID, flag: int) -> None:
        self.uuid: uuid.UUID = uuid
        self.flag: int = flag

    def __repr__(self) -> str:
        return f"uuid={self.uuid}, flag={self.flag}"


class Server:
    def __init__(self, ip_addr: str, port: int) -> None:
        self.ip_addr: str = ip_addr
        self.port: int = port
        self.connection_queue: queue.Queue[socket.socket] = queue.Queue() 
        self.connected: bool = False
        self.conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def establish_connection(self):
        listener = threading.Thread(
            target=self._worker_thread,
            daemon=True
        )
        listener.start()

    def _worker_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
            logging.info("Establishing server connection with message sender...")
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.ip_addr, self.port))
            server_sock.listen(3)

            conn, addr = server_sock.accept()
            logging.info(f"Server connection with {addr} successfully established.")
            self.connection_queue.put(conn)

    def read_msg(self) -> Message:
        while not self.connected:
            try:
                self.conn = self.connection_queue.get(timeout = 1.0)
                self.connected = True
            except queue.Empty:
                continue

        raw = self.conn.recv(1024)
        json_string = raw.decode("utf-8")
        data = json.loads(json_string)
        msg: Message = Message(data["uuid"], data["flag"])
        return msg



class Client:
    def __init__(self, ip_addr: str, port: int) -> None:
        self.ip_addr: str = ip_addr
        self.port: int = port
        self.client_socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def connect(self) -> None:
        try:
            logging.info("Establishing client connection with message recepient...")
            self.client_socket.connect((self.ip_addr, self.port))
            logging.info("Client connection successfully established.")
        except Exception as e:
            logging.error(f"Could not establish client connection: {e}")
            sys.exit(1)

    def send(self, msg: Message) -> None:
        json_string = json.dumps(msg.__dict__)
        self.client_socket.sendall(json_string.encode("utf-8"))
        logging.info(f"Sent: {msg}")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(message)s",
        level=logging.INFO,
        handlers=[
            logging.FileHandler(os.path.join(ROOT_PATH, "log.txt"), mode="w"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    my_ip = ""
    my_port = 0
    other_ip = ""
    other_port = 0

    try:
        logging.info(f"Reading config file...")
        with open(os.path.join(ROOT_PATH, "config.txt"), "r") as f:
            lines = f.readlines()
            line1 = lines[0].split(",")
            line2 = lines[1].split(",")

            my_ip = line1[0]
            my_port = int(line1[1][:-1])

            other_ip = line2[0]
            other_port = int(line2[1][:-1])
    except Exception as e:
        logging.error(f"Could not read config file:\n{e}")
        sys.exit(1)

    server = Server(my_ip, my_port)
    client = Client(other_ip, other_port)

    server.establish_connection()  # non blocking
    input("Press enter when everyone is ready...")  # wait for everyone before
    client.connect()

    my_uuid = uuid.uuid4()
    logging.info(f"Starting process, my uuid={my_uuid}")

    msg = Message(my_uuid, 0)
    curr_state = 0

    client.send(msg)

    while curr_state == 0:
        msg = server.read_msg()

        if msg.uuid > my_uuid:
            # greater, forward the message
            curr_state = msg.flag
            logging.info(f"Recieved: {msg}, greater, {curr_state}")
            client.send(msg)
        elif msg.uuid == my_uuid:
            # equal, set the state to 1 and exit the loop
            curr_state = 1
            logging.info(f"Received: {msg}, equal, {curr_state}")
        else:
            # less, ignore the message
            logging.info(f"Recieved: {msg}, less, {curr_state}")

    # send final message where leader is decided
    msg.flag = 1
    logging.info(f"Leader is decided to {msg.uuid}")
    client.send(msg)

    sys.exit(0)
