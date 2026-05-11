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
- PyNaCl library (for cryptographic signatures)

---

## Python 3.11 Setup

### Check Python version
```bash
python3.11 --version
````

If not installed:

### Linux (Arch)

```bash
sudo pacman -S python
```

### Windows

Download from:
[https://www.python.org/downloads/release/python-3110/](https://www.python.org/downloads/release/python-3110/)

During installation:

* Enable “Add Python to PATH”

Verify:

```bash
python --version
```

---

## Setup Virtual Environment

```bash
python3.11 -m venv venv
```

### Activate environment

### Linux / macOS / WSL

```bash
source venv/bin/activate
```

### Windows (PowerShell)

```bash
venv\Scripts\activate
```

---

## Install Dependencies

### Required: PyNaCl

```bash
pip install pynacl
```

---

## Running a Node

```bash
./Run.sh 5000 test1/node1/node-list.txt
```

This will:

* Start a node on port 5000
* Load peers from node list
* Wait for transactions or consensus triggers

---

## Sending Transactions

### Linux / Arch (jq + netcat)

Install tools:

```bash
sudo pacman -S jq openbsd-netcat
```

Send transactions:

```bash
jq -c '.[]' test1/input.json | while read line; do
  echo "$line" | nc localhost 5000
done
```

---

### Windows (Git Bash or WSL recommended)

Install:

* jq: [https://github.com/jqlang/jq/releases](https://github.com/jqlang/jq/releases)
* ncat (from Nmap): [https://nmap.org/download.html](https://nmap.org/download.html)

Run:

```bash
jq -c ".[]" test1/input.json | while read line; do
  echo "$line" | ncat localhost 5000
done
```

---



## Debugging in VS Code

### 1. Select Python interpreter

* Press Ctrl + Shift + P
* Search: Python: Select Interpreter
* Select:

Linux:

```
./venv/bin/python
```

Windows:

```
venv\Scripts\python.exe
```

---

### 2. launch.json

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

### 3. Debug Flow

1. Set breakpoints in node.py or main.py
2. Press F5 to start node
3. Run transaction sender in another terminal
4. Observe:

   * transaction validation
   * mempool updates
   * block creation
   * consensus execution

---

## Expected Execution Flow

1. Node starts and listens on port
2. Transactions arrive and are validated
3. Valid transactions go into mempool
4. When mempool is non-empty:

   * node creates a block
   * consensus runs across peers
5. A block is chosen
6. Block is committed
7. Blockchain is printed

---

## Notes

* Only peer request phase uses 2 second timeout
* Unresponsive peers are marked crashed
* Blockchain prints after each commit
* Ensure all peers in node list are running for consensus

```
```
