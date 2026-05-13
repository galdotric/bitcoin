import json, socket, struct, threading
from transac import Transaction
from block import Blockchain, Block


def _recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _recv_msg(conn):
    header = _recv_exact(conn, 2)
    if header is None:
        return None
    length = struct.unpack("!H", header)[0]
    body = _recv_exact(conn, length)
    if body is None:
        return None
    return json.loads(body.decode("utf-8"))


def _send_msg(conn, obj):
    data = json.dumps(obj, sort_keys=True, indent=2).encode("utf-8")
    conn.sendall(struct.pack("!H", len(data)) + data)


class Node:
    def __init__(self, peers=None, send_fn=None, recv_fn=None):
        self.blockchain = Blockchain()
        self.peers = peers or []
        self.mempool = []
        self.current_proposal = None
        self.received_proposal = []
        self.failed_peers = set()
        self._send_msg = send_fn or _send_msg
        self._recv_msg = recv_fn or _recv_msg

    def handle_node_msg(self, message: dict, reply_sock=None) -> bool:
        msg_type = message.get("type")
        payload = message.get("payload")

        if msg_type == "transaction":
            result = self.handle_transaction(payload)
            # Spec §4.1: respond with true/false on the same connection
            if reply_sock is not None:
                try:
                    ack = json.dumps(result).encode("utf-8")
                    reply_sock.sendall(struct.pack("!H", len(ack)) + ack)
                except Exception:
                    pass
            return result
        elif msg_type == "values":
            return self.handle_values(payload, reply_sock=reply_sock)
        return False

    def handle_values(self, payload, reply_sock=None):
        if self.current_proposal is None:
            self.create_block()

        if reply_sock is not None:
            response = {
                "type": "values",
                "payload": self.current_proposal.to_dict() if self.current_proposal else {}
            }
            try:
                self._send_msg(reply_sock, response)
            except Exception:
                pass
        return True

    def handle_transaction(self, payload: dict) -> bool:
        tx = Transaction(
            sender=payload["sender"],
            message=payload["message"],
            nonce=payload["nonce"],
            signature=payload["signature"]
        )
        if tx.is_valid(self.blockchain, self.mempool):
            self.mempool.append(tx)
            self.print_event(tx)
            # Broadcast to peers so all nodes have the tx before consensus
            self._broadcast_tx(tx)
            # Run consensus in background — don't block the connection handler
            threading.Thread(target=self.run_consensus, args=(self.peers,), daemon=True).start()
            return True
        return False

    def _broadcast_tx(self, tx):
        for host, port in self.peers:
            peer = (host, port)
            if peer in self.failed_peers:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(1.0)
                    s.connect((host, port))
                    self._send_msg(s, {"type": "transaction", "payload": tx.to_dict()})
            except Exception:
                pass  # don't mark crashed just for broadcast failure

    def create_block(self):
        if not self.mempool:
            return None
        last_block = self.blockchain.get_last_block()
        new_block = Block(
            index=last_block.index + 1,
            transactions=self.mempool.copy(),
            previous_hash=last_block.get_hash()
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
            }, sort_keys=True, indent=2))

    def run_consensus(self, peers):
        if not self.current_proposal:
            self.create_block()
        proposals = []
        if self.current_proposal:
            proposals.append(self.current_proposal)

        for host, port in peers:
            peer = (host, port)
            if peer in self.failed_peers:
                continue
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(2.0)
                    s.connect((host, port))
                    self._send_msg(s, {
                        "type": "values",
                        "payload": self.current_proposal.to_dict() if self.current_proposal else {}
                    })
                    response = self._recv_msg(s)
                    if response and response.get("type") == "values":
                        data = response.get("payload")
                        if data and isinstance(data, dict) and data.get("index"):
                            proposals.append(Block.from_dict(data))
            except (socket.timeout, ConnectionRefusedError, OSError):
                self.failed_peers.add(peer)
                continue

        decided = self.decide_on_block(proposals)
        if decided:
            self.commit_block(decided)
        self.current_proposal = None

    def decide_on_block(self, proposals):
        if not proposals:
            return None
        non_empty = [b for b in proposals if len(b.transactions) > 0]
        candidates = non_empty if non_empty else proposals
        return min(candidates, key=lambda b: b.get_hash())