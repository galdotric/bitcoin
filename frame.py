import struct

def send_framed_json(sock, data_dict):
    """
    1. Convert dict to JSON string.
    2. Encode to UTF-8.
    3. Prepend 2-byte length (big-endian).
    4. Send.
    """
    pass

def receive_framed_json(sock):
    """
    1. Read exactly 2 bytes.
    2. Unpack to get length 'N'.
    3. Read exactly 'N' bytes.
    4. Decode and parse JSON.
    """
    pass
