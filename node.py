from typing import List
from transac import Transaction
from block import Block, Blockchain
from socket import socket, AF_INET

class Node:
    def __init__(self, node_address: str, peer_file: str) -> None:
        self.node_address = node_address
        self.mempool: List[Transaction] = []
        self.peers: List[str] = []
        self.load_peers(peer_file)
        self.blockchain = Blockchain()
        self.server_socket = None
        self.peer_sockets: dict[str, socket] = {}

    #transaction handling
    def receive_transaction(self, transaction: Transaction):
        pass

    def validate_transaction(self, transaction: Transaction):
        pass
    

    #block handling
    def propose_block(self):
        pass

    def receive_block(self, block: Block):
        pass

    #network
    def load_peers(self, peer_file: str):
        """Read peer addresses from file and populate self.peers"""
        pass

    def send_block_2_peers(self, block: Block):
        pass

    def handle_incoming_peer_msg(self, msg):
        pass

    def connect_2_peers(self):
        pass

    def accept_peer_connections(self):
        pass

    def detect_peer_failure(self):
        pass

    def get_last_block(self):
        pass

    def run_concensus_round(self):
        pass

    def broadcast_values(self):
        pass

    def handle_client_transaction(self):
        pass

