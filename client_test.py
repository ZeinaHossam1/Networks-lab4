from ReliableUDP import ReliableUDP
import time

print("Starting Client ...")
client = ReliableUDP()

# Connect to the server
if client.connect(("127.0.0.1", 8080)):
    print("\n--- Connection Successful! Sending Data ---")

    # TEST 1: Normal Delivery
    print("\n[TEST 1] Sending a normal message...")
    client.send(b"Hello from the client. This is a reliable UDP test.")
    time.sleep(2)

    # TEST 2: Simulate Packet Loss 
    print("\n[TEST 2] Simulating packet loss...")
    client.send(b"This packet will be dropped once.", simulate_loss=True)
    time.sleep(2)

    # TEST 3: Simulate Packet Corruption 
    print("\n[TEST 3] Simulating packet corruption...")
    client.send(b"This packet will have a false checksum.", simulate_corruption=True)
    time.sleep(2)

    # TEST 4: Duplicate Packets
    print("\n[TEST 4] Simulating duplicate packets...")
    client.send(b"This message is sent twice, but should only appear once.", simulate_duplicate=True)
    time.sleep(2)

    print("\n--- Disconnecting ---")
    client.disconnect()