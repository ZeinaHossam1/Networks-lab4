from ReliableUDP import ReliableUDP

print("--- Starting Server ---")
server = ReliableUDP()

# Accept the connection
server.accept_connection("127.0.0.1", 8080)

print("\nWaiting for incoming data...")

# Keep listening forever until the client tells us to stop
while True:
    data, addr, seq, ack, syn, ack_flag, fin = server.receive()
    
    # 1. Check if the client wants to disconnect
    if fin == 1:
        print("\n[SERVER] Disconnect signal (FIN) received from client. Breaking loop...")
        break # This exits the while loop!
    
    # 2. If it's normal data, print it
    if data:
        print(f"[SERVER] Received message: {data.decode('utf-8')}")

print("\n--- Disconnecting ---")
server.disconnect()