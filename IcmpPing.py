from socket import *
import os
import sys
import struct
import time
import select

ICMP_ECHO_REQUEST = 8


def checksum(string):
    csum = 0
    countTo = (len(string) // 2) * 2
    count = 0

    while count < countTo:
        thisVal = string[count + 1] * 256 + string[count]
        csum = csum + thisVal
        csum = csum & 0xffffffff
        count = count + 2

    if countTo < len(string):
        csum = csum + string[len(string) - 1]
        csum = csum & 0xffffffff

    csum = (csum >> 16) + (csum & 0xffff)
    csum = csum + (csum >> 16)
    answer = ~csum
    answer = answer & 0xffff
    answer = answer >> 8 | (answer << 8 & 0xff00)

    return answer


def receiveOnePing(mySocket, ID, timeout, destAddr):
    timeLeft = timeout

    while True:
        startedSelect = time.time()
        whatReady = select.select([mySocket], [], [], timeLeft)
        howLongInSelect = time.time() - startedSelect

        if whatReady[0] == []:
            return "Request timed out."

        timeReceived = time.time()
        recPacket, addr = mySocket.recvfrom(1024)

        # Extract ICMP header (skip 20-byte IP header)
        icmpHeader = recPacket[20:28]
        type, code, checksum_recv, packetID, sequence = struct.unpack("bbHHh", icmpHeader)

        if packetID == ID:
            bytesInDouble = struct.calcsize("d")
            timeSent = struct.unpack("d", recPacket[28:28 + bytesInDouble])[0]
            rtt = timeReceived - timeSent
            return f"Reply from {destAddr}: time={round(rtt*1000, 2)} ms"

        timeLeft -= howLongInSelect
        if timeLeft <= 0:
            return "Request timed out."


def sendOnePing(mySocket, destAddr, ID):
    myChecksum = 0

    # Create dummy header
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    data = struct.pack("d", time.time())

    # Calculate checksum
    myChecksum = checksum(header + data)

    # Fix byte order
    myChecksum = htons(myChecksum)

    # Repack header with checksum
    header = struct.pack("bbHHh", ICMP_ECHO_REQUEST, 0, myChecksum, ID, 1)
    packet = header + data

    mySocket.sendto(packet, (destAddr, 1))


def doOnePing(destAddr, timeout):
    icmp = getprotobyname("icmp")

    try:
        mySocket = socket(AF_INET, SOCK_RAW, icmp)
    except PermissionError:
        return "Error: You need to run this program as Administrator/root."

    myID = os.getpid() & 0xFFFF

    sendOnePing(mySocket, destAddr, myID)
    delay = receiveOnePing(mySocket, myID, timeout, destAddr)

    mySocket.close()
    return delay


def ping(host, timeout=1):
    dest = gethostbyname(host)
    print(f"Pinging {host} [{dest}] using Python:\n")

    while True:
        delay = doOnePing(dest, timeout)
        print(delay)
        time.sleep(1)


# Run the ping
if __name__ == "__main__":
 #   ping("127.0.0.1")      # Localhost
 #   ping("google.com")     # North America
 #   ping("bbc.co.uk")      # Europe
     ping("google.co.jp")   # Asia