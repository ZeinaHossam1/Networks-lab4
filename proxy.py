import socket
from ReliableUDP import ReliableUDP

# Configuration
PROXY_HOST = "127.0.0.1"
PROXY_PORT = 8081  # The browser will connect to this port
UDP_SERVER_PORT = 8080  # ReliableUDP server is listening here


def start_proxy():
    # 1. Set up a standard TCP socket to listen to the web browser
    tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcp_socket.bind((PROXY_HOST, PROXY_PORT))
    tcp_socket.listen(5)

    print(f"--- Proxy Server Running ---")
    print(f"Point your browser to: http://{PROXY_HOST}:{PROXY_PORT}/index.html")

    while True:
        # 2. Wait for the browser to connect
        browser_conn, browser_addr = tcp_socket.accept()
        print(f"\n[PROXY] Browser connected from {browser_addr}")

        try:
            # 3. Receive the standard TCP HTTP request from the browser
            request_data = browser_conn.recv(4096)
            if not request_data:
                browser_conn.close()
                continue

            print(
                "[PROXY] Received request from browser. Connecting to ReliableUDP Server..."
            )

            # 4. Spin up a ReliableUDP client to talk to your custom server
            udp_client = ReliableUDP()
            if udp_client.connect((PROXY_HOST, UDP_SERVER_PORT)):

                # Forward the browser's request over UDP
                print("[PROXY] Forwarding request over UDP...")
                udp_client.send(request_data)

                # Wait for the UDP server to reply
                response_data, addr, seq, ack, syn, ack_flag, fin = udp_client.receive()

                # 5. Send the server's response back to the browser over TCP
                print(
                    "[PROXY] Received response from UDP server. Forwarding to browser..."
                )
                browser_conn.sendall(response_data)

                # Disconnect the UDP client cleanly
                udp_client.disconnect()
            else:
                print("[PROXY] Failed to connect to ReliableUDP server.")
                error_response = b"HTTP/1.0 502 Bad Gateway\r\n\r\nFailed to reach backend UDP server."
                browser_conn.sendall(error_response)

        except Exception as e:
            print(f"[PROXY] Error: {e}")
        finally:
            # 6. Close the TCP connection with the browser
            browser_conn.close()


if __name__ == "__main__":
    start_proxy()
