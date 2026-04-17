import ed25519
from block import Blockchain


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
        # scan backwards to find latest transaction from this sender
        for block in reversed(blockchain.chain):
            for tx in block.transactions:
                if tx.sender == self.sender:
                    confirmed = tx.nonce
                    expected_nonce = confirmed + 1 + sum(
                        1 for t in mempool
                        if t.sender == self.sender and t is not self
                    )
                    return self.nonce == expected_nonce

        # if sender has no previous transactions
        expected_nonce = 0 + sum(
            1 for t in mempool if t.sender == self.sender
        )

        return self.nonce == expected_nonce


    def verify_signature(self):
        try:
            msg_bytes = f"{self.sender}{self.message}{self.nonce}".encode()

            public_key_bytes = bytes.fromhex(self.sender)
            signature_bytes = bytes.fromhex(self.signature)

            vk = ed25519.VerifyingKey(public_key_bytes)
            vk.verify(signature_bytes, msg_bytes)

            return True
        except Exception:
            print("error from transac verify_signature")
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
