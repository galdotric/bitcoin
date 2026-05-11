import socket
import threading
import json
import sys
import time
from node import Node

def handle_client(conn, addr, node):
    try:
        from node import _recv_msg, _send_msg

        msg = _recv_msg(conn)
        if msg:
            response = node.handle_node_msg(msg)

            # only send response if Node returns something
            if response is not None:
                _send_msg(conn, response)

    except Exception as e:
        print(f"Error handling connection from {addr}: {e}")
    finally:
        conn.close()

def server_loop(port, node):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', port))
        s.listen(5)
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr, node), daemon=True).start()

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 main.py <Port-Server> <Node-List-File>")
        sys.exit(1)

    port = int(sys.argv[1])
    node_list_file = sys.argv[2]
    peers = []
    node = Node()
    with open(node_list_file, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                peer_host, peer_port = line.strip().split(':')
                peer_port = int(peer_port)
                # Don't add ourselves as a peer
                if not ((peer_host == '127.0.0.1' or peer_host == 'localhost') and peer_port == port):
                    peers.append((peer_host, peer_port))
                #gives node access to peers in handle_transaction method of Node class
                node.peers = peers

    server_thread = threading.Thread(target=server_loop, args=(port, node), daemon=True)
    server_thread.start()


    # Main loop: Trigger consensus when transactions arrive or on a timer
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    main()