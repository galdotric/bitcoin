import socket
import threading
import time
import math

class Peer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        self.sock = None
        self.is_crashed = False  # Mark as crashed if 2s timeout is hit [cite: 363]
        self.lock = threading.Lock()

    def connect(self):
        """Initial connection should not have an immediate timeout[cite: 357, 359]."""
        pass

    def send_message(self, msg_dict: dict):
        """Must prepend 2-byte big-endian length prefix."""
        pass

    def receive_message(self) -> dict:
        """Read 2 bytes for length, then read N bytes for JSON[cite: 245]."""
        pass

    def set_consensus_timeout(self):
        """Set socket timeout to 2 seconds for consensus phase[cite: 360, 368]."""
        if self.sock:
            self.sock.settimeout(2.0)

    def disable_timeout(self):
        """Set timeout to None after consensus round completes[cite: 365, 368]."""
        if self.sock:
            self.sock.settimeout(None)

class NetworkHandler:
    def __init__(self, node, port: int):
        self.node = node
        self.port = port
        self.listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listen_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def start_server(self):
        """Bind and listen. Start a new thread for each accepted connection[cite: 51]."""
        pass

    def handle_peer(self, peer_sock):
        """
        Continuous loop to receive messages.
        If 'transaction', validate and add to mempool[cite: 109, 124].
        If 'values', pass to ConsensusManager[cite: 110, 418].
        """
        pass



class ConsensusManager:
    def __init__(self, node):
        self.node = node
        self.f = math.ceil(len(node.peers_list) / 2) - 1 # Max tolerated crashes [cite: 390]

    def run_consensus_loop(self):
        """
        Thread loop that waits for:
        1. Non-empty mempool OR 2. Incoming 'values' request[cite: 402, 404].
        """
        while True:
            # Step 1: Triggering
            # Step 2: Create Proposal (even if empty) [cite: 407, 411]
            # Step 3: Broadcast Phase
            self.broadcast_and_collect()
            # Step 4: Decision logic
            self.decide_and_commit()

    def broadcast_and_collect(self):
        """
        - Set 2s timeout on all active peer sockets[cite: 415].
        - Send 'values' message[cite: 414].
        - Collect responses. Mark as crashed if timeout occurs[cite: 417].
        - Reset timeouts to None after phase[cite: 365].
        """
        pass

    def decide_and_commit(self):
        """
        - Ignore empty blocks if a non-empty one exists[cite: 420].
        - Choose block with lexicographically smallest current_hash[cite: 421].
        - Append to chain and print to stdout[cite: 285, 423].
        """
        pass
