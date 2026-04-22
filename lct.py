from nacl.signing import SigningKey
from node import Node
import json


def create_signed_tx(sk, message, nonce):
    sender_hex = sk.verify_key.encode().hex()
    msg = f"{sender_hex}{message}{nonce}".encode()
    sig = sk.sign(msg).signature.hex()

    return {
        "sender": sender_hex,
        "message": message,
        "nonce": nonce,
        "signature": sig
    }


def print_chain(node):
    print("\n=== FINAL BLOCKCHAIN ===")
    for block in node.blockchain.chain:
        print(json.dumps(block.to_dict(), indent=2, sort_keys=True))
        print("hash:", block.current_hash)
        print()


def print_tx_summary(txs):
    print("\n=== TRANSACTION SUMMARY ===")
    for tx in txs:
        print({
            "sender": tx["sender"][:4] + "...",  # shorten for readability
            "nonce": tx["nonce"]
        })


def main():
    node = Node()

    # multiple users
    sk1 = SigningKey.generate()
    sk2 = SigningKey.generate()

    txs = [
        create_signed_tx(sk1, "A1", 0),
        create_signed_tx(sk2, "B1", 0),
        create_signed_tx(sk1, "A2", 1),
        create_signed_tx(sk2, "B2", 1),
        create_signed_tx(sk1, "A3", 2),
    ]

    print_tx_summary(txs)

    print("\n=== SENDING TRANSACTIONS (BLOCK 1) ===")
    # first 3 transactions go into block 1
    for tx in txs[:3]:
        node.handle_node_msg({
            "type": "transaction",
            "payload": tx
        })

    block1 = node.create_block()
    if block1:
        node.commit_block(block1)

    print("\n=== SENDING TRANSACTIONS (BLOCK 2) ===")
    # last 2 transactions go into block 2
    for tx in txs[3:]:
        node.handle_node_msg({
            "type": "transaction",
            "payload": tx
        })

    block2 = node.create_block()
    if block2:
        node.commit_block(block2)

    print_chain(node)


if __name__ == "__main__":
    main()