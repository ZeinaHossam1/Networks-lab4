from ReliableUDP import ReliableUDP


def handle_http_request(raw_request):
    """Parses the HTTP request and generates an appropriate HTTP response."""
    request_text = raw_request.decode("utf-8")
    print(f"\n[SERVER] Received Request:\n{request_text}")

    # Split the request into lines to parse headers and body
    lines = request_text.split("\r\n")
    if not lines or not lines[0]:
        return build_response(400, "Bad Request")

    # The first line contains Method, Path, and Protocol (e.g., "GET / HTTP/1.0")
    request_line = lines[0].split()
    if len(request_line) < 3:
        return build_response(400, "Bad Request")

    method, path, protocol = request_line[0], request_line[1], request_line[2]

    # Handle GET Method
    if method == "GET":
        if path == "/" or path == "/index.html":
            body = "<html><body><h1>200 OK</h1><p>Welcome to the ReliableUDP HTTP Server!</p></body></html>"
            return build_response(200, body)
        else:
            body = "<html><body><h1>404 NOT FOUND</h1><p>The requested page does not exist.</p></body></html>"
            return build_response(404, body)

    # Handle POST Method
    elif method == "POST":
        # Find the empty line that separates headers from the body
        try:
            body_index = lines.index("") + 1
            post_body = "\n".join(lines[body_index:])
        except ValueError:
            post_body = "[No Body Found]"

        response_body = f"<html><body><h1>200 OK</h1><p>POST data received successfully: {post_body}</p></body></html>"
        return build_response(200, response_body)

    else:
        return build_response(404, "Method not supported.")


def build_response(status_code, body):
    """Constructs a valid HTTP 1.0 response with headers."""
    status_text = "OK" if status_code == 200 else "NOT FOUND"

    # Standard HTTP 1.0 Headers
    response = f"HTTP/1.0 {status_code} {status_text}\r\n"
    response += "Server: ReliableUDP_Custom_Server\r\n"
    response += "Content-Type: text/html\r\n"
    response += f"Content-Length: {len(body)}\r\n"
    response += "Connection: close\r\n\r\n"  # Double CRLF indicates end of headers
    response += body

    return response.encode("utf-8")


print("--- Starting HTTP Server over ReliableUDP ---")
server = ReliableUDP()

# Accept connection on localhost:8080
server.accept_connection("127.0.0.1", 8080)

while True:
    data, addr, seq, ack, syn, ack_flag, fin = server.receive()

    if fin == 1:
        print("\n[SERVER] Disconnect signal received. Shutting down...")
        break

    if data:
        # Process the request and generate HTTP response
        http_response = handle_http_request(data)

        print(f"\n[SERVER] Sending Response (Seq: {server.current_seq_num})...")
        server.send(http_response)

print("\n--- Server Stopped ---")
