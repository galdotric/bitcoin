import socket
import struct
import threading
import json
import sys
import time


def _recv_exact(conn, n):
    buf = b""
    while len(buf) < n:
        chunk = conn.recv(n - len(buf))
        if not chunk:
            return None
        buf += chunk
    return buf


def _recv_msg(conn):
    header = _recv_exact(conn, 2)
    if header is None:
        return None
    length = struct.unpack("!H", header)[0]
    body = _recv_exact(conn, length)
    if body is None:
        return None
    return json.loads(body.decode("utf-8"))


def _send_msg(conn, obj):
    data = json.dumps(obj, sort_keys=True, indent=2).encode("utf-8")
    conn.sendall(struct.pack("!H", len(data)) + data)


def handle_client(conn, addr, node):
    try:
        while True:
            msg = _recv_msg(conn)
            if not msg:
                break
            node.handle_node_msg(msg, reply_sock=conn)
    except Exception:
        pass
    finally:
        conn.close()


def server_loop(server_sock, node):
    while True:
        try:
            conn, addr = server_sock.accept()
            threading.Thread(target=handle_client, args=(conn, addr, node), daemon=True).start()
        except Exception:
            break


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 main.py <Port-Server> <Node-List-File>", file=sys.stderr)
        sys.exit(1)

    port = int(sys.argv[1])
    node_list_file = sys.argv[2]

    # Bind port FIRST before slow imports so autograder sees it immediately
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', port))
    server_sock.listen(5)

    from node import Node

    peers = []
    with open(node_list_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                peer_host, peer_port_str = line.rsplit(':', 1)
                peer_port = int(peer_port_str)
                if not ((peer_host in ('127.0.0.1', 'localhost')) and peer_port == port):
                    peers.append((peer_host, peer_port))

    node = Node(peers, _send_msg, _recv_msg)

    server_thread = threading.Thread(target=server_loop, args=(server_sock, node), daemon=True)
    server_thread.start()

    # Keep alive until killed by autograder
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()