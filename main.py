import sys
import time
from node import Node # Assuming your Node class is in node.py

def main():
    # 1. Parse command line arguments provided by the autograder's Run.sh
    if len(sys.argv) != 3:
        print("Usage: python3 main.py <Port-Server> <Node-List-File>")
        sys.exit(1)

    port = int(sys.argv[1])
    peer_file = sys.argv[2]

    # For local testing and the autograder, the host is typically localhost
    node_address = f"127.0.0.1:{port}"

    # 2. Initialize the Node with the parsed arguments
    my_node = Node(node_address=node_address, peer_file=peer_file)

    # 3. Start the node (this should spin up the Server thread and Consensus thread)
    my_node.start()

    # 4. Keep the main thread alive. 
    # Because your server and consensus loops should be running in daemon threads,
    # if the main thread exits, the whole program shuts down.
    try:
        while True:
            time.sleep(1) # Sleep to prevent high CPU usage
    except KeyboardInterrupt:
        print("\nShutting down node...")
        sys.exit(0)

if __name__ == "__main__":
    main()
