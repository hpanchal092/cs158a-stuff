import sys
import time
import uuid
import json
import socket
import threading
import queue
import logging
import os

ROOT_PATH = os.path.dirname(os.path.abspath(__file__))

BUFFER_SIZE = 1024


class Message:
    def __init__(self, uuid: uuid.UUID, flag: int) -> None:
        self.uuid: uuid.UUID = uuid
        self.flag: int = flag

    def __repr__(self) -> str:
        return f"uuid={self.uuid}, flag={self.flag}"


class MessageEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Message):
            return {"uuid": str(o.uuid), "flag": o.flag}
        return super().default(o)


class Server:
    def __init__(self, ip_addr: str, port: int) -> None:
        self.ip_addr: str = ip_addr
        self.port: int = port
        self.message_queue: queue.Queue[Message | None] = queue.Queue()

    def establish_connection(self):
        # listen for connections on a seperate thread to not block main thread
        listener = threading.Thread(target=self._worker_thread, daemon=True)
        listener.start()

    def _worker_thread(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            logging.info("Establishing server connection with message sender...")
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.ip_addr, self.port))
            server_socket.listen(3)

            conn, addr = server_socket.accept()
            logging.info(f"Server connection with {addr} successfully established.")

            buffer = ""
            decoder = json.JSONDecoder()

            while True:
                chunk = conn.recv(BUFFER_SIZE)
                if not chunk:
                    self.message_queue.put(None)  # if we receive nothing, peer most likely closed conenction
                    return
                buffer += chunk.decode("utf-8")

                while True:
                    buffer = buffer.lstrip()
                    if not buffer:
                        break
                    try:
                        data, end = decoder.raw_decode(buffer)
                    except ValueError:
                        break  # partial object, wait for more bytes
                    buffer = buffer[end:]
                    self.message_queue.put(Message(uuid.UUID(data["uuid"]), data["flag"]))

    def read_msg(self) -> Message:
        msg = self.message_queue.get()
        if msg is None:
            raise ConnectionError("peer closed the connection")
        return msg


class Client:
    def __init__(self, ip_addr: str, port: int) -> None:
        self.ip_addr: str = ip_addr
        self.port: int = port
        self.client_socket: socket.socket = socket.socket(
            socket.AF_INET, socket.SOCK_STREAM
        )

    def connect(self) -> None:
        try:
            logging.info("Establishing client connection with message recepient...")
            self.client_socket.connect((self.ip_addr, self.port))
            logging.info("Client connection successfully established.")
        except Exception as e:
            logging.error(f"Could not establish client connection: {e}")
            sys.exit(1)

    def send(self, msg: Message) -> None:
        json_string = json.dumps(msg, cls=MessageEncoder)
        try:
            self.client_socket.sendall(json_string.encode("utf-8"))
            logging.info(f"Sent: {msg}")
        except Exception as e:
            logging.warning(f"Could not send {msg}: {e}")


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

    logging.info(f"Reading config file...")
    with open(os.path.join(ROOT_PATH, "config.txt"), "r") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

        my_ip, my_port = lines[0].split(",")
        other_ip, other_port = lines[1].split(",")
        my_port, other_port = int(my_port), int(other_port)

    server = Server(my_ip, my_port)
    client = Client(other_ip, other_port)

    server.establish_connection()  # non blocking
    time.sleep(0.5)
    input("\nPress enter when everyone is ready...\n")  # wait for everyone before
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
            logging.info(f"Received: {msg}, greater, {curr_state}")
            client.send(msg)
        elif msg.uuid == my_uuid:
            # equal, set the state to 1 and exit the loop
            curr_state = 1
            msg.flag = 1
            logging.info(f"Received: {msg}, equal, {curr_state}")
            client.send(msg)
        else:
            # less, ignore the message
            logging.info(f"Received: {msg}, less, {curr_state}")

    logging.info(f"Leader is decided to {msg.uuid}")

    sys.exit(0)
