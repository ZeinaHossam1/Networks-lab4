from ReliableUDP import ReliableUDP
import time


def build_get_request(path):
    """Builds a standard HTTP GET request."""
    request = f"GET {path} HTTP/1.0\r\n"
    request += "Host: 127.0.0.1\r\n"
    request += "User-Agent: ReliableUDP_Client\r\n\r\n"  # Blank line ends headers
    return request.encode("utf-8")


def build_post_request(path, data):
    """Builds a standard HTTP POST request with a body."""
    request = f"POST {path} HTTP/1.0\r\n"
    request += "Host: 127.0.0.1\r\n"
    request += "User-Agent: ReliableUDP_Client\r\n"
    request += "Content-Type: text/plain\r\n"
    request += (
        f"Content-Length: {len(data)}\r\n\r\n"  # Blank line separates headers from body
    )
    request += data
    return request.encode("utf-8")


print("Starting HTTP Client over ReliableUDP...")
client = ReliableUDP()

if client.connect(("127.0.0.1", 8080)):
    print("\n--- Connection Successful! ---")

    # TEST 1: Valid GET Request (Should return 200 OK)
    print("\n[TEST 1] Sending valid GET request (/index.html)...")
    get_req = build_get_request("/index.html")
    client.send(get_req)

    # Wait for the server's HTTP response
    response_data, addr, seq, ack, syn, ack_flag, fin = client.receive()
    print("\n[CLIENT] Response from Server:")
    print(response_data.decode("utf-8"))
    time.sleep(2)

    # TEST 2: Invalid GET Request (Should return 404 NOT FOUND)
    print("\n[TEST 2] Sending invalid GET request (/missingpage.html)...")
    get_req_404 = build_get_request("/missingpage.html")
    client.send(get_req_404)

    response_data, addr, seq, ack, syn, ack_flag, fin = client.receive()
    print("\n[CLIENT] Response from Server:")
    print(response_data.decode("utf-8"))
    time.sleep(2)

    # TEST 3: POST Request
    print("\n[TEST 3] Sending POST request with data...")
    post_data = "Hello! This is payload data from the POST request."
    post_req = build_post_request("/submit_form", post_data)
    client.send(post_req)

    response_data, addr, seq, ack, syn, ack_flag, fin = client.receive()
    print("\n[CLIENT] Response from Server:")
    print(response_data.decode("utf-8"))
    time.sleep(2)

    print("\n--- Disconnecting ---")
    client.disconnect()
