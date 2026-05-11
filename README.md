````markdown
# Blockchain Node Project

## Overview
This project implements a simple distributed blockchain node that:
- Accepts transactions over TCP
- Stores them in a mempool
- Builds blocks
- Runs a basic consensus protocol with peers
- Maintains a blockchain state

---

## Requirements

- Python 3.11
- Virtual environment (recommended)
- `pynacl` library (for cryptographic signatures)

---

## Setup

### 1. Create and activate virtual environment
```bash
python3.11 -m venv venv
source venv/bin/activate
````

---

### 2. Install dependencies

#### Install PyNaCl (required)

```bash
pip install pynacl
```

If you later add more dependencies:

```bash
pip install -r requirements.txt
```

---

## Running a Node

Start a node using:

```bash
./Run.sh 5000 test1/node1/node-list.txt
```

This will:

* Start a server on port `5000`
* Load peers from `node-list.txt`
* Wait for transactions or consensus triggers

---

## Sending Transactions

Use the provided input file:

```bash
while read line; do
  echo "$line" | nc localhost 5000
done < test1/input.json
```

This sends each JSON transaction one by one to the node.

---

## Debugging in VS Code

### 1. Select Python interpreter

* Press `Ctrl + Shift + P`
* Search: **Python: Select Interpreter**
* Select:

```
./venv/bin/python
```

---

### 2. Create launch configuration

Create `.vscode/launch.json`:

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

---

### 3. Debug flow

1. Set breakpoints in `node.py` or `main.py`
2. Press `F5` to start the node
3. In another terminal, run the transaction sender command above
4. Observe:

   * transaction validation
   * mempool updates
   * block creation
   * consensus execution

---

## Expected Execution Flow

1. Node starts and listens on a port
2. Transactions arrive → validated → added to mempool
3. When mempool is non-empty:

   * node creates a block
   * consensus is triggered across peers
4. A block is decided
5. Block is committed to the blockchain
6. Blockchain state is printed

---

## Notes

* Only peer request phase uses timeouts (2 seconds)
* Unresponsive peers are marked as crashed
* Blockchain is printed after each committed block
* Ensure all nodes in `node-list.txt` are running for full consensus testing

```
```
