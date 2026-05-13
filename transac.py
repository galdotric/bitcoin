from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError
import json

class Transaction:
    def __init__(self, sender: str, message: str, nonce: int, signature: str):
        self.sender = sender  # 64-char hex public key
        self.message = message
        self.nonce = nonce
        self.signature = signature


    def validate_field_formats(self):
        if not isinstance(self.sender, str) or len(self.sender) != 64:
            return False
        try:
            int(self.sender, 16)
        except ValueError:
            return False

        if not isinstance(self.message, str) or len(self.message) > 70:
            return False
        if not all(c.isalnum() or c.isspace() for c in self.message):
            return False

        if not isinstance(self.nonce, int) or self.nonce < 0:
            return False

        if not isinstance(self.signature, str) or len(self.signature) != 128:
            return False
        try:
            int(self.signature, 16)
        except ValueError:
            return False

        return True


    def verify_key(self):
        try:
            bytes.fromhex(self.sender)
            return True
        except Exception:
            return False


    def verify_nonce(self, blockchain, mempool):
        # Calculate how many tx from this sender are already in mempool
        # (Excluding self)
        pending_others = 0
        for t in mempool:
            if t.sender == self.sender and t is not self:
                pending_others += 1

        for block in reversed(blockchain.chain):
            for tx in block.transactions:
                # Handle both Transaction objects and network dictionaries
                curr_sender = tx.sender if hasattr(tx, 'sender') else tx['sender']
                curr_nonce = tx.nonce if hasattr(tx, 'nonce') else tx['nonce']
                
                if curr_sender == self.sender:
                    return self.nonce == curr_nonce + 1 + pending_others

        # Sender has no transactions in the chain yet
        # Expected = 0 (for first ever tx) + Pending in Pool
        return self.nonce == 0 + pending_others


    def verify_signature(self):
        try:
            tx_to_verify = {
                "sender": self.sender,
                "message": self.message,
                "nonce": self.nonce
            }

            msg_bytes = json.dumps(
                tx_to_verify,
                sort_keys=True
            ).encode("utf-8")

            public_key_bytes = bytes.fromhex(self.sender)
            signature_bytes = bytes.fromhex(self.signature)

            vk = VerifyKey(public_key_bytes)
            vk.verify(msg_bytes, signature_bytes)

            return True

        except BadSignatureError:
            return False
        except Exception as e:
            return False


    def is_valid(self, blockchain, mempool):
        return (
            self.validate_field_formats() and
            self.verify_key() and
            self.verify_nonce(blockchain, mempool) and
            self.verify_signature()
        )



    def to_dict(self):
        return {
            "sender": self.sender,
            "message": self.message,
            "nonce": self.nonce,
            "signature": self.signature
        }

    def from_dict(tx_dict):
        return Transaction(
            message=tx_dict["message"],
            nonce=tx_dict["nonce"],
            sender=tx_dict["sender"],
            signature=tx_dict["signature"]
        )