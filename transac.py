import json
import ed25519
from block import Blockchain
class Transaction:
    def __init__(self, sender: str, message: str, nonce: int, signature: str) -> None:
        self.sender = sender
        self.message = message
        self.nonce = nonce
        self.signature = signature


    def validate_field_formats(self):
        # 1. Sender: Must be 64-char string. 
        # (The spec implies hex; checking if hex ensures it's valid for Ed25519)
        if not isinstance(self.sender, str) or len(self.sender) != 64:
            return False
        try:
            int(self.sender, 16) # Verify it is valid hex
        except ValueError:
            return False

        if not isinstance(self.message, str) or len(self.message) > 70:
            return False
        if not all(char.isalnum() or char.isspace() for char in self.message):
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

    def check_nonce_logic(self, blockchain: Blockchain):
        last_nonce = blockchain.get_confirmed_nonce(self.sender)
        return self.nonce == last_nonce +1
        
    def to_dict(self):
        return {
            "sender" : self.sender,
            "message" : self.message,
            "nonce" : self.nonce,
            "signature" : self.signature
        }

    def verify_signature(self):
        try:
            data = f"{self.sender}{self.message}{self.nonce}".encode('utf-8')
            vk_bytes = bytes.fromhex(self.sender)
            sig_bytes = bytes.fromhex(self.signature)

            vk = ed25519.VerifyingKey(vk_bytes)
            vk.verify(sig_bytes, data)
            return True
        except Exception:
            print("error from transac verify_signature")
            return False

    def is_valid(self,blockchain):
       return (self.validate_field_formats() and
                self.verify_key() and
                self.check_nonce_logic(blockchain) and
                self.verify_signature()
               )
