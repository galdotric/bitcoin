import json
from typing import List
from transac import Transaction
import hashlib
class Block:
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str) -> None:
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.current_hash = None

    def compute_current_hash(self):
        block_dict = self.to_dict()

        cannonical_json = json.dumps(
            block_dict,
            sort_keys=True,
            indent = 2,
            separators=(',', ': ')
        )

        return hashlib.sha256(cannonical_json.encode('utf-8')).hexdigest()

    def validate_prev_hash(self, previous_block):
        return self.previous_hash == previous_block.get_hash()

    def to_dict(self):
        """
        Converts the block to a dictionary for hashing and network transmission.
        Note: current_hash is NOT included in the dictionary used for hashing.
        """
        return {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash
        }

    def get_hash(self):
        return self.current_hash


class Blockchain:
    def __init__(self) -> None:
        self.chain: List[Block] = []
        self.nonce_tracker: dict[str, int] = {}

        #gensis block
        genesis_prev_hash = "0"*64
        genesis_block = Block(
            index = 1,
            transactions = [],
            previous_hash = genesis_prev_hash
        )
        genesis_block.current_hash = genesis_block.compute_current_hash()
        #add to chain as root block
        self.chain.append(genesis_block)

    def add_block(self, block: Block)-> bool:
        """Appends block and updates the confirmed state."""
        if self.validate_block(block):
            self.chain.append(block)
            self.update_nonce_tracker(block)
            return True
        return False

    def validate_block(self, block: Block)-> bool:
        """Checks if the block links correctly to the current chain."""
        last_block = self.get_last_block()
        
        # 1. Check index sequence
        if block.index != last_block.index + 1:
            return False
        
        # 2. Check hash linkage
        if block.previous_hash != last_block.current_hash:
            return False
            
        return True

    def get_last_block(self)->Block:
        return self.chain[-1] if self.chain else None

    def update_nonce_tracker(self,block: Block):
        for tx in block.transactions:
            self.nonce_tracker[tx.sender] = tx.nonce

    def is_valid_next_block(self, block: Block):
        if not self.validate_block(block):
            return False
        return True

    def get_confirmed_nonce(self, sender_pk):
        return self.nonce_tracker.get(sender_pk, -1)
