# Blockchain Node: Peer-to-Peer Ledger in Python

This is a **distributed blockchain node** written in Python. Each node listens on a TCP port and accepts **Ed25519-signed transactions**. It checks each transaction's format, nonce and signature, keeps valid ones in a **mempool** and forwards them to its peers. It then runs a **one-round consensus**: it collects every peer's proposed block and commits the one with the lowest hash. Nodes print each transaction they accept and each block they commit as JSON, so the output of several nodes can be compared.

---

## Contents

1. [Quick start](#1-quick-start)
2. [Usage](#2-usage)
3. [Files](#3-files)
4. [Architecture](#4-architecture)
5. [Wire protocol](#5-wire-protocol)
6. [Transaction rules](#6-transaction-rules)
7. [Blocks and the chain](#7-blocks-and-the-chain)
8. [Consensus](#8-consensus)
9. [Design decisions](#9-design-decisions)
10. [Testing](#10-testing)
11. [Known limitations](#11-known-limitations)

---

## 1. Quick start

```sh
python3 -m venv venv && source venv/bin/activate
pip install pynacl
./Run.sh 5000 test1/node1/node-list.txt
```

---

## 2. Usage

### Requirements

| Tool | Version |
|---|---|
| Python | 3.11 or newer (also runs on 3.14) |
| PyNaCl | Any recent version (`pip install pynacl`) |

Arch Linux: `sudo pacman -S python`. Windows: install from [python.org](https://www.python.org/downloads/) and tick **Add Python to PATH**.

### Setting up

```sh
python3 -m venv venv
source venv/bin/activate          # Windows PowerShell: venv\Scripts\activate
pip install pynacl
```

### Running a node

```
./Run.sh <port> <node-list-file>
```

`Run.sh` runs `exec python3 -u main.py "$@"`. The `-u` turns off output buffering, so the JSON appears as soon as it is printed, and `exec` makes the shell become the Python process, so stopping `Run.sh` (Ctrl+C or `kill`) stops the node too.

| Argument | Meaning |
|---|---|
| `port` | TCP port this node listens on (all interfaces) |
| `node-list-file` | One peer per line as `host:port`. A line naming this node's own port on `localhost` / `127.0.0.1` is skipped |

```
localhost:5001
localhost:5002
```

Start each node in the list in its own terminal. Consensus only includes peers that are running.

### Sending transactions

Every message must start with a **2-byte length prefix** (see [Wire protocol](#5-wire-protocol)), so plain `nc` doesn't work. Use this short Python sender. It waits 1 second between messages, because the node only gives consistent results when transactions arrive one at a time (see [Known limitations](#11-known-limitations)):

```python
# send_tx.py: send each message in a JSON file to a node, print the replies
import json, socket, struct, sys, time

port, path = int(sys.argv[1]), sys.argv[2]
for msg in json.load(open(path)):
    data = json.dumps(msg).encode()
    with socket.create_connection(("localhost", port)) as s:
        s.sendall(struct.pack("!H", len(data)) + data)
        n = struct.unpack("!H", s.recv(2))[0]
        print(s.recv(n).decode())        # true or false
    time.sleep(1)                        # let consensus finish before the next one
```

```sh
python3 send_tx.py 5000 test1/input.json
```

### Output

Each accepted transaction is printed as:

```json
{
  "payload": {
    "message": "First Transaction",
    "nonce": 0,
    "sender": "d7581e61…d630",
    "signature": "816eb000…8407"
  },
  "type": "transaction"
}
```

Each committed block is printed as:

```json
{
  "current_hash": "aee8a6e9…422d",
  "index": 2,
  "previous_hash": "70debc4f…768d",
  "transactions": [ { "message": "First Transaction", "nonce": 0, "sender": "…", "signature": "…" } ]
}
```

### Debugging in VS Code

Select `./venv/bin/python` as the interpreter (**Ctrl+Shift+P → Python: Select Interpreter**), then add this to `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Run Node",
      "type": "python",
      "request": "launch",
      "program": "main.py",
      "args": ["5000", "test1/node1/node-list.txt"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

Set breakpoints in `node.py`, press **F5**, then run the sender in another terminal.

---

## 3. Files

| File | Role |
|---|---|
| `main.py` | Entry point: binds the port, reads the peer list, accepts connections (one thread each), and does the message framing |
| `node.py` | `Node`: handles messages, forwards transactions, runs consensus, prints events |
| `block.py` | `Block` (hashing, serialisation) and `Blockchain` (genesis block, validation, mempool cleanup) |
| `transac.py` | `Transaction`: format, nonce and signature checks |
| `Run.sh` | Starts a node with unbuffered output |
| `test1/` … `test4/` | Test cases (see [Testing](#10-testing)) |

---

## 4. Architecture

### 4.1 Components

| Component | Receives | Does | Sends to |
|---|---|---|---|
| `main.py` | TCP connections from clients and peers | Accepts each connection on its own thread and decodes length-prefixed messages | `Node.handle_node_msg` |
| `Node` (`node.py`) | Decoded `transaction` and `values` messages | Validates, keeps the mempool, forwards transactions, runs consensus | Peers (`transaction`, `values`), stdout (JSON events) |
| `Transaction` (`transac.py`) | A transaction plus the chain and mempool | Checks format, nonce and signature | Returns valid or not |
| `Blockchain` (`block.py`) | A chosen block | Checks it links to the last block, appends it, cleans the mempool | Returns committed or not |

`Transaction` and `Blockchain` hold the rules and do no network I/O; `main.py` and `Node` do all of it.

### 4.2 State held by a node

| Field | Holds |
|---|---|
| `blockchain.chain` | The list of committed blocks, starting with the genesis block |
| `mempool` | Valid transactions that are not yet in a block |
| `current_proposal` | The block this node is proposing in the current round, or `None` |
| `peers` | `(host, port)` pairs from the node list |
| `failed_peers` | Peers that timed out or refused a connection during consensus. They are skipped from then on |

---

## 5. Wire protocol

Every message, in both directions, is:

```
┌──────────────────┬──────────────────────────┐
│ length (2 bytes, │ UTF-8 JSON body          │
│ big-endian)      │ (length bytes)           │
└──────────────────┴──────────────────────────┘
```

| Message | Sent by | Reply |
|---|---|---|
| `{"type": "transaction", "payload": {sender, message, nonce, signature}}` | Clients and peers | The JSON value `true` (accepted) or `false` (rejected), with the same framing |
| `{"type": "values", "payload": <block or {}>}` | A node running consensus | `{"type": "values", "payload": <this node's proposal or {}>}` |

A connection can carry several messages one after another. It is closed when the other side closes it.

---

## 6. Transaction rules

A transaction is accepted only if **all** of these hold:

| Field | Rule |
|---|---|
| `sender` | 64 hex characters (an Ed25519 public key) |
| `message` | At most 70 characters; every character must be a letter, digit or whitespace (Python's `isalnum()` / `isspace()`, so non-English letters and tabs also pass) |
| `nonce` | An integer ≥ 0, equal to the **next expected nonce** for this sender (below) |
| `signature` | 128 hex characters, and a valid Ed25519 signature by `sender` over `json.dumps({"sender", "message", "nonce"}, sort_keys=True)` |

**Next expected nonce** = (the nonce of the sender's first transaction in the newest block that has one, + 1, or 0 if the sender has none in the chain) + (the number of the sender's other transactions already in the mempool). A sender can therefore have several transactions pending, as long as they are numbered in order.

An accepted transaction is added to the mempool, printed, sent to every peer (1 s timeout), and starts a consensus round in a background thread.

---

## 7. Blocks and the chain

| Field | Meaning |
|---|---|
| `index` | Position in the chain. The genesis block is `1` |
| `transactions` | The transactions in this block |
| `previous_hash` | `current_hash` of the block before it. For genesis it is 64 zeros |
| `current_hash` | SHA-256 of `json.dumps({index, transactions, previous_hash}, sort_keys=True, indent=2)` |

The genesis block is created by every node, has no transactions and is never printed.

A block is committed only if:

1. `index` is the last block's index + 1,
2. `previous_hash` equals the last block's `current_hash`, and
3. `current_hash` matches a fresh hash of its contents.

After a commit, the block's transactions are removed from the mempool, and every remaining transaction is checked again (their nonces may no longer be valid).

---

## 8. Consensus

Each round has a single phase. For example, with node A and peers B and C:

1. A accepts a transaction and forwards it to B and C.
2. A builds a proposal: one block holding its whole mempool.
3. A sends `values` with its proposal to B; B replies with its own proposal.
4. A sends `values` to C; C doesn't reply within 2 s, so A marks C as failed.
5. A picks the lowest hash among the non-empty proposals, validates it, commits it and prints it.

| Step | Detail |
|---|---|
| Propose | If this node has no proposal yet, it makes a block from its whole mempool |
| Collect | It sends `values` to each peer that hasn't failed, with a **2 s** timeout, and keeps each non-empty block it gets back |
| Mark failures | A timeout, refused connection or other socket error adds the peer to `failed_peers` for good |
| Decide | Among proposals that contain transactions, it picks the one with the **lowest `current_hash`**. If every proposal is empty, it picks the lowest of those |
| Commit | It validates the chosen block (see [§7](#7-blocks-and-the-chain)), appends it, prints it, and clears the proposal |

A node that receives `values` with no proposal of its own makes one from its mempool first. If its mempool is empty it answers with `{}`. The proposal it receives in the request is ignored.

---

## 9. Design decisions

| Decision | Alternatives considered | Why this one |
|---|---|---|
| 2-byte length-prefixed JSON | Newline-delimited JSON | No ambiguity about where a message ends, even when a message contains newlines (the output is pretty-printed) |
| Bind the port **before** importing `node` (and PyNaCl) | Import everything first | The test runner checks the port right after starting the node, and the crypto import is slow |
| Lowest hash wins | Longest chain, voting | Every node that sees the same set of proposals picks the same block, with no extra round of messages |
| One thread per connection plus a consensus thread per transaction | A single event loop | A slow peer or a long consensus round never blocks new transactions from being accepted |
| Forward transactions before consensus | Rely on proposals only | Peers already have the transaction in their mempool, so their proposals usually match |
| Canonical JSON (`sort_keys=True`) for signing and hashing | Python `repr`, hand-ordered fields | Every node serialises the same block to the same bytes, so the hashes agree |

---

## 10. Testing

Each `testN/` folder has:

| Path | Contents |
|---|---|
| `input.json` | A list of messages to send |
| `nodeK/node-list.txt` | Peers of node K |
| `nodeK/port-server.txt` | The port node K listens on |
| `expected/outputK.txt` | What node K should print |
| `expected/output.txt` | All nodes' expected output together |

| Test | Nodes | Ports |
|---|---|---|
| `test1` | 3 | 5000–5002 |
| `test2` | 2 | 5000–5001 |
| `test3` | 1 | 8300 |
| `test4` | 1 | 58504 |

To run test 1 by hand:

```sh
./Run.sh 5000 test1/node1/node-list.txt > out1.txt &
./Run.sh 5001 test1/node2/node-list.txt > out2.txt &
./Run.sh 5002 test1/node3/node-list.txt > out3.txt &
sleep 2
python3 send_tx.py 5000 test1/input.json
sleep 5; kill %1 %2 %3
for n in 1 2 3; do
  diff out$n.txt <(tail -n +2 test1/expected/output$n.txt | sed '/^$/d') && echo "node $n: OK"
done
```

`tail -n +2` drops the `--- Node N ---` header line and `sed` drops the blank line at the end of each expected file.


---

## 11. Known limitations

- **Not safe under concurrent traffic.** Every accepted transaction starts its own consensus thread, and the threads share the mempool and proposal **without any locking**. Delivered one at a time (even 0.2 s apart), all four tests pass every run. Sent back to back, nodes commit different blocks, and the same transaction sent 20 times at once is accepted several times and replayed in later blocks.
- **Peer blocks are trusted.** `validate_block` checks only the block's index, previous hash and types, not the signatures or nonces of its transactions, so a misbehaving peer can get a forged transaction committed.
- **Nonce replay.** After a block holding nonces 0 and 1 from one sender, `verify_nonce` still expects 1, so the committed nonce-1 transaction is accepted again.
- **Failed peers never come back.** Once a peer misses the 2 s deadline it is skipped for the rest of the run, even if it recovers.
- **Messages are limited to 65 535 bytes** because of the 2-byte length prefix. A block with many transactions could go over this.
- **Errors are swallowed.** A transaction with missing fields closes the connection with no reply, a message with an unknown `type` gets no reply at all, and `validate_block`'s `sys.exit(1)` only ends the thread it runs in, not the node.
