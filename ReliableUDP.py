import socket
import struct
import time
import zlib 

class ReliableUDP:

    def __init__(self, timeout=2.0):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Default timeout for the socket
        self.socket.settimeout(timeout)
        # We start with no destination. connect() will fill this in later
        self.server_address = None 
        # Track the sequence number (starts at 0)
        self.current_seq_num = 0
        # What sequence number the receiver is expecting next
        self.expected_seq_num = 0

    def build_packet(self, seq_num, ack_num, syn_flag, ack_flag, fin_flag, data=b""):
        #Initialize header format for the pack function
        header_format = "!IIBBBI"
        
        dummy_header=struct.pack(header_format,seq_num, ack_num, syn_flag, ack_flag, fin_flag,0)
        dummy_packet=dummy_header+data      #To calculate checksum for everything
        
        value=self.calculate_checksum(dummy_packet)
        header=struct.pack(header_format,seq_num, ack_num, syn_flag, ack_flag, fin_flag,value)
        packet=header+data
        
        return packet

    def calculate_checksum(self, data: bytes) -> int:
        """
        Calculates a 32-bit Cyclic Redundancy Check (CRC) for the given byte array.
        """
        # zlib.crc32 generates the mathematical checksum.
        # We apply a bitwise AND (& 0xffffffff) to ensure the result is always 
        # treated as an unsigned 32-bit integer across all Python versions.
        checksum = zlib.crc32(data) & 0xffffffff
        
        return checksum
    
    # 3-way handshake
    def connect(self,server_address):
        self.server_address=server_address
        # (1) SYN packet
        # seq_num=0, ack_num=0, SYN=1, ACK=0, FIN=0, data=empty
        SYN_packet=self.build_packet(0,0,1,0,0,b"")

        # start a timer and wait for ACK
        max_retries=6
        retries=0
        
        while retries<max_retries:
            try:
                self.socket.sendto(SYN_packet,self.server_address)
                print(f"Sent SYN packet. Waiting for SYN-ACK... (Attempt {retries + 1})")
                # (2) waiting for SYN-ACK packet
                r_data, addr, r_seq, r_ack, r_syn, r_ack_flag, r_fin = self.receive() # If an ACK wasn't received in 2 secs a timeout occurs and it returns an error

                print("SYN-ACK received!")
                break
            
            except socket.timeout:
                print("Packet lost.Retransmitting...")
                retries+=1

        if retries==max_retries:
            print("Connection failed: Server is unresponsive.")
            return False
        
        # (3) ACK packet
        # seq_num=1, ack_num=0, SYN=0 ACK=1, FIN=0, data=empty
        ACK_packet=self.build_packet(1,0,0,1,0,b"")
        self.socket.sendto(ACK_packet,self.server_address)
        print("Connection established!")
        return True
    
    def accept_connection(self,host,port):
        # 1. Bind the physical socket to the IP and Port
        self.socket.bind((host, port))
        print(f"Server listening on {host}:{port}...")
        
        while True:
            # (2) listen for SYN packet
            # We don't want the server to timeout while waiting for a new client
            self.socket.settimeout(None)
            r_data, addr, r_seq, r_ack, r_syn, r_ack_flag, r_fin = self.receive() # If a SYN-ACK wasn't received in 2 secs a timeout occurs and it returns an error
            
            if(r_syn==1):
                print("SYN received from {addr}! Sending SYN-ACK...")
                self.server_address=addr

                # (3) Send SYN-ACK (Seq=0, Ack=1, SYN=1, ACK=1)
                SYN_ACK_packet=self.build_packet(0, 1, 1, 1, 0, b"")
                self.socket.sendto(SYN_ACK_packet, self.server_address)

                # (4) listen for ACK packet
                while True:
                    try:
                        self.socket.settimeout(2.0)
                        r_data, addr, r_seq, r_ack, r_syn, r_ack_flag, r_fin = self.receive() 
                        if(r_ack_flag==1 and r_syn==0):
                            print("Final ACK received. Connection established!")
                            return 
                        elif r_syn == 1:
                            # The client timed out and resent the SYN. Resend SYN-ACK
                            print("Duplicate SYN received. Resending SYN-ACK...")
                            self.socket.sendto(SYN_ACK_packet, self.server_address)
                            continue

                    except socket.timeout:
                        print("Handshake failed. Client did not send final ACK.")
                        break

    def receive(self, buffer_size=1024):

        while True:
            # (1) The socket listens for incoming data
            try:
                raw_packet, sender_address = self.socket.recvfrom(buffer_size)       #Catches the entire combined packet   
            except ConnectionResetError:
                # The remote server closed early. 
                raise socket.timeout
        

            # (2) We slice the raw packet to seperate the data from the header
            header=raw_packet[:15]
            data=raw_packet[15:]
            seq, ack, syn, ack_flag, fin, received_checksum = struct.unpack("!IIBBBI", header)

            # (3) recreate the full original packet
            dummy_header = struct.pack("!IIBBBI", seq, ack, syn, ack_flag, fin, 0)
            dummy_packet = dummy_header + data
            
            # (4) Calculate checksum for recreated packet
            calculated_checksum = self.calculate_checksum(dummy_packet)
            
            # (5) compare with received checksum
            if calculated_checksum==received_checksum:
                #checking which type of data it is
                if syn == 0 and (fin == 1 or data != b""):
                    
                    print(f"Data received (Seq: {seq}). Sending ACK...")
                    # 1. Build the ACK packet
                    # Set ack_num to the seq we just received 
                    ack_packet = self.build_packet(self.current_seq_num,seq,0,1,0,data=b"")
                    # 2. Send the ACK back to the sender
                    self.socket.sendto(ack_packet, sender_address)

                    # 3. Check for duplicate packets
                    if seq == self.expected_seq_num:
                        # This is a new packet Update expected seq_num-->toggle
                        self.expected_seq_num = 1 - self.expected_seq_num
                        return data, sender_address, seq, ack, syn, ack_flag, fin
                    else:
                        # This is a duplicate packet. 
                        print(f"Duplicate packet (Seq: {seq}) dropped")
                        continue
                
                # If it's a SYN or FIN packet, just return it normally so connect() and accept_connection() work
                return data, sender_address, seq, ack, syn, ack_flag, fin
            
            else:
                print("Corrupted packet dropped!")


    def send(self,data,simulate_loss=False, simulate_corruption=False):
        # (1) create the packet to be sent
        packet=self.build_packet(self.current_seq_num, 0, 0, 1, 0, data)
        
        # (2) start sending and 
        max_retries=6
        retries=0

        while retries<max_retries:
            try: 
                if simulate_loss and retries == 0:
                    print(f"\n[SIMULATION] Dropping packet (Seq: {self.current_seq_num}). Waiting for timeout...")
                    # Intentionally skip the sendto() command!
                    
                elif simulate_corruption and retries == 0:
                    print(f"\n[SIMULATION] Sending CORRUPTED packet (Seq: {self.current_seq_num})...")
                    # Flip bits in the last byte to ruin the checksum math
                    corrupted_packet = packet[:-1] + bytes([packet[-1] ^ 0xFF])
                    self.socket.sendto(corrupted_packet, self.server_address)

                else:
                    self.socket.sendto(packet,self.server_address)
                    print(f"Sent packet. Waiting for ACK... (Attempt {retries + 1})")
                # Stop and wait
                # (3) waiting for ACK packet
                r_data, addr, r_seq, r_ack, r_syn, r_ack_flag, r_fin=self.receive() # If an ACK wasn't received in 2 secs a timeout occurs and it returns an error

                # (3a) ack is received and is correct
                if(r_ack_flag==1 and r_ack==self.current_seq_num):
                    print("Packet successfully delivered and acknowledged!")
                    self.current_seq_num = 1 - self.current_seq_num
                    break

                # (3b) Mismatched ACK
                else:
                    print("Received mismatched ACK. Retransmitting...")
                    retries+=1
                    continue
            
            except socket.timeout:
                print("Packet lost.Retransmitting...")
                retries+=1

        # (4) max retries reached 
        if retries==max_retries:
            print("Maximum retries reached. Destination server is unresponsive.")
            return False

    # Disconnect function to close the connection
    def disconnect(self):
        print("Initiating disconnect...")

        # Send fin packet 
        fin_packet = self.build_packet(self.current_seq_num, 0, 0, 0, 1, b"")
        self.socket.sendto(fin_packet, self.server_address)
        
        try:
            # Wait for the server to ACK our disconnect
            r_data, addr, r_seq, r_ack, r_syn, r_ack_flag, r_fin = self.receive()
            print("Disconnect ACK received. Closing socket.")
        except socket.timeout:
            print("No response to FIN. Forcing close.")
            
        self.socket.close()
        





