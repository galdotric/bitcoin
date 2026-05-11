import json
from typing import List
from transac import Transaction
import hashlib
import sys

class Block:
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str) -> None:
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.current_hash = self.compute_current_hash()

    def compute_current_hash(self):
        block_dict = self.to_dict()

        canonical_json = json.dumps(
            block_dict,
            sort_keys=True,
            indent=2,
            separators=(',', ': ')
        )

        return hashlib.sha256(canonical_json.encode('utf-8')).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "transactions": [tx.to_dict() for tx in self.transactions],
            "previous_hash": self.previous_hash
        }

    def get_hash(self):
        return self.current_hash
    
    def from_dict(block_dict):
        transactions = [Transaction.from_dict(tx_dict) for tx_dict in block_dict["transactions"]]
        return Block(
            index=block_dict["index"],
            transactions=transactions,
            previous_hash=block_dict["previous_hash"]
        )
    



class Blockchain:
    def __init__(self) -> None:
        self.chain: List[Block] = []

        # Genesis block
        genesis_block = Block(
            index=1,
            transactions=[],
            previous_hash="0" * 64
        )
        genesis_block.current_hash = genesis_block.compute_current_hash()
        self.chain.append(genesis_block)

    def add_block(self, block: Block, mempool: List[Transaction]) -> bool:
        if not self.validate_block(block, mempool):
            return False

        self.chain.append(block)

        self._update_mempool(block, mempool)

        return True

    def validate_block(self, block: Block, mempool: List[Transaction]) -> bool:
        last_block = self.get_last_block()

        #index check
        if block.index != last_block.index + 1:
            return False
        #hash linkage
        if block.previous_hash != last_block.current_hash:
            return False
        #validate all transactions in block
        processed_txs = []
        for tx_obj in block.transactions:
            if not isinstance(tx_obj, Transaction):
                sys.exit(1)
            processed_txs.append(tx_obj)

        # Update block with transaction objects
        block.transactions = processed_txs
            
        #validate that the block's current_hash was computed honestly
        if block.current_hash != block.compute_current_hash():
            return False

        return True

    def _update_mempool(self, block: Block, mempool: List[Transaction]):
        # remove confirmed transactions
        confirmed_sigs = {tx.signature for tx in block.transactions}
        mempool[:] = [tx for tx in mempool if tx.signature not in confirmed_sigs]

        valid_remaining = []

        for tx in mempool:
            if tx.is_valid(self, mempool):
                valid_remaining.append(tx)

        mempool[:] = valid_remaining

    def get_last_block(self) -> Block:
        return self.chain[-1]

