import json, socket
from transac import Transaction
from block import Blockchain, Block
class Node:
    def __init__(self):
        self.blockchain = Blockchain()
        self.peers = []
        self.mempool = []
        self.current_proposal = None
        self.received_proposal = []
        self.failed_peers = set()
    
    def handle_node_msg(self, message: dict) -> bool:
        msg_type = message.get("type")
        payload = message.get("payload")

        if msg_type == "transaction":
            return self.handle_transaction(payload)

        #values part written here
        elif msg_type == "values":
            return self.handle_values(payload)

        return False

    def handle_values(self, payload):
        # ensure we have a proposal
        if self.current_proposal is None:
            self.create_block()

        #respond with your proposal
        response = {
            "type": "values",
            "payload": self.current_proposal.to_dict() if self.current_proposal else []
        }

        print(json.dumps(response, sort_keys=True, indent=2))
        return True

    def handle_transaction(self, payload: dict) -> bool:
        #make transaction instance
        tx = Transaction(
            sender = payload["sender"],
            message = payload["message"],
            nonce = payload["nonce"],
            signature = payload["signature"]
        )
        if tx.is_valid(self.blockchain, self.mempool):
            self.mempool.append(tx)
            self.print_event(tx)
            self.run_consensus(self.peers)
            return True
        return False

    def create_block(self):
        #check mempool
        if not self.mempool:
            return None
        mempool = self.mempool
        blockchain = self.blockchain
        
        last_block = blockchain.get_last_block()
        new_block = Block(
            index = last_block.index+1,
            transactions = mempool.copy(),
            previous_hash = last_block.get_hash()
        )
        self.current_proposal = new_block
        return new_block

    def commit_block(self, block):
        result = self.blockchain.add_block(block, self.mempool)
        if result:
            self.print_event(block)
        return result
    
    def print_event(self, obj):
        if isinstance(obj, Transaction):
            print(json.dumps({
                "type": "transaction",
                "payload": obj.to_dict()
            }, sort_keys=True, indent=2))

        elif isinstance(obj, Block):
            print(json.dumps({
                "current_hash": obj.get_hash(),
                "index": obj.index,
                "previous_hash": obj.previous_hash,
                "transactions": [t.to_dict() for t in obj.transactions]
            }, indent=2))
    
    #connections
    def run_consensus(self, peers):
        if not self.current_proposal:
            self.create_block()
        proposals = []
        if self.current_proposal:
            proposals.append(self.current_proposal)
        for host, port in peers:
            peer = (host, port)
            # skip known crashed peers
            if peer in self.failed_peers:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2.0)
                    s.connect((host, port))

                    _send_msg(s, {
                        "type": "values",
                        "payload": {}
                    })
                    response = _recv_msg(s)
                    if response and response.get("type") == "values":
                        data = response.get("payload")
                        if data:
                            proposals.append(Block.from_dict(data))
            except (socket.timeout, ConnectionRefusedError, OSError):
                self.failed_peers.add(peer)
                continue
        # decision
        decided = self.decide_on_block(proposals)
        if decided:
            self.commit_block(decided)
        self.current_proposal = None

    def decide_on_block(self, proposals):
        if not proposals:
            return None

        # Filter: If at least one block has transactions, ignore empty ones
        non_empty_blocks = [b for b in proposals if len(b.transactions) > 0]
        
        candidate_pool = non_empty_blocks if non_empty_blocks else proposals

        # Tie-breaker: Lexicographical smallest current_hash
        # .get_hash() should return the hex string
        decided_block = min(candidate_pool, key=lambda b: b.get_hash())
        
        return decided_block
    
def _recv_msg(sock):
    data = sock.recv(4096)
    if not data:
        return None

    return json.loads(data.decode())


def _send_msg(sock, msg):
    data = json.dumps(msg).encode()
    sock.sendall(data)



