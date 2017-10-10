import socket
import struct
import os

def getNetworkIp():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.connect(('<broadcast>', 0))
    return s.getsockname()[0]

def generate_string(serial_no):
    """Create request string for inverter.

    The request string is build from several parts. The first part is a
    fixed 4 char string; the second part is the reversed hex notation of
    the s/n twice; then again a fixed string of two chars; a checksum of
    the double s/n with an offset; and finally a fixed ending char.

    Args:
        serial_no (int): Serial number of the inverter

    Returns:
        str: Information request string for inverter
    """
    #frame = (V4 headCode) + (dataFieldLength) + (contrlCode) + (command) + (checksum) + (endCode)
    frame_hdr = '\x68\x02\x41\xb1' #from SolarMan / new Omnik app
    command = '\x01\x00'
    endCode = '\x16'

    serial_hex = bytearray(hex(serial_no)[2:] * 2)
    tar = bytearray([serial_hex[i:i + 2].decode('hex') for i in reversed(range(0, len(serial_hex), 2))])

    frame = frame_hdr + tar + command + '\x87' + endCode

    checksum = 0
    frame_bytes = bytearray(frame)
    for i in range(1, len(frame_bytes) - 2, 1):
        checksum += frame_bytes[i] & 255
    frame_bytes[len(frame_bytes) - 2] = int((checksum & 255))
    return "".join(map(chr, frame_bytes))

def expand_path(path):
    """
    Expand relative path to absolute path.

    Args:
        path: file path

    Returns: absolute path to file

    """
    if os.path.isabs(path):
        return path
    else:
        return os.path.dirname(os.path.abspath(__file__)) + "/" + path

def getLoggers():
    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((getNetworkIp(), 48899))
    # Set a timeout so the socket does not block indefinitely when trying to receive data.
    sock.settimeout(3)
    # Set the time-to-live for messages to 1 so they do not go past the local network segment.
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    SendData = "WIFIKIT-214028-READ" # Lotto/TM = "AT+YZAPP=214028,READ"

    gateways = ''
    try:
        # Send data to the broadcast address
        sent = sock.sendto(SendData, ('<broadcast>', 48899))
        # Look for responses from all recipients
        while True:
            try:
                data, server = sock.recvfrom(1024)
            except socket.timeout:
                break
            else:
                if (data == SendData): continue #skip sent data
                a = data.split(',')
                wifi_ip, wifi_mac, wifi_sn = a[0],a[1],a[2]
                if (len(gateways)>1):
                    gateways = gateways+','
                gateways = gateways+wifi_ip+','+wifi_sn
    
    finally:
        sock.close()
        return gateways
