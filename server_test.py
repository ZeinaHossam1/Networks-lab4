from ReliableUDP import ReliableUDP 

print("Starting Server...")
server = ReliableUDP()

# Accept the connection on localhost, port 8080
server.accept_connection("127.0.0.1", 8080)

print("\nWaiting for incoming data...")
# Receive loop handles the ACK and duplicate checking in the background
data, addr, seq, ack, syn, ack_flag, fin = server.receive()

# Decode the bytes back to a string so we can read it
print(f"\n[SERVER] Received message from client: {data.decode('utf-8')}")

print("\n--- Disconnecting ---")
server.disconnect()