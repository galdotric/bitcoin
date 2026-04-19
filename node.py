import json
from transac import Transaction
from block import Blockchain, Block
class Node:
    def __init__(self):
        self.blockchain = Blockchain()
        self.mempool = []
        self.current_proposal = None
        self.received_proposal = []
    
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
        # payload = list of blocks from peer

        # ensure we have a proposal
        if self.current_proposal is None:
            self.create_block()

        #(future step) store peer proposals if needed
        peer_blocks = payload
        #respond with your proposal
        response = {
            "type": "values",
            "payload": [self.current_proposal.to_dict()] if self.current_proposal else []
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
        #check validation of transaction
        if tx.is_valid(self.blockchain, self.mempool):
            #if valid add tx to mempool
            self.mempool.append(tx)

            print(json.dumps({
                "type": "transaction",
                "payload": tx.to_dict()
            }, sort_keys= True, indent=2))
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
        #called at end of successfull concensus round
        return self.blockchain.add_block(block, self.mempool)
