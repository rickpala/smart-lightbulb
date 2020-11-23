#!/usr/local/bin/python3

# Ricky Palaguachi
# rsp84
# CS 356 - 007

# iot-client.py

import sys
import socket
import string
import random
import struct
import os
import re
import json
from datetime import datetime
import time


byte_fmt_str = "!BBHBBBB"
def send_info_req():
    req
    pass

def send_update_req():
    pass

def parse_cmdline_args():
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        print("Bad cmd-line arguments.")
        quit()

    return host, port

def parse_user_input_to_bytes():
    # Ask for status
    status = int(input("Status? "))
    is_device_info_req = (status == 0)
    if is_device_info_req:
        send_info_req()
        return

    mode = int(input("Mode? "))
    static_mode = (mode == 0) 
    gradient_mode = (mode == 1)
    
    if static_mode:
        num_colors_expected = 1
    elif gradient_mode:
        num_colors_expected = 2
    else:
        # Throw MODE_UNSUPPORTED_ERROR
        pass

    colors = []
    while len(colors) < num_colors_expected:
        color = input(f"Color {len(colors)} (R,G,B,L):")
        color_tpl = eval(color)

        colors.append(color_tpl)        

    msg_type = 0
    err_num = 0
    msg_id = random.randint(0, 2**16)

    # Print the request data
    print(f"Message Type: 0")
    print(f"Message ID: {msg_id}")
    print(f"Number of Colors: {num_colors_expected}")
    print(f"Status: {status}")
    print(f"Mode: {mode}")
    for i, color in enumerate(colors):
        print(f"Color {i} RGBL: {str(color)}\n")


    # Pack structure to be sent
    # Send bytes in the following order:
    # - B Message Type
    # - B Error Number
    # - H Message ID
    # - B Number of Colors
    # - x Pad Byte
    # - B Status
    # - B Mode
    # - 4B * N RGBL Values (1B Each)

    buf  = bytes()
    buf += struct.pack(
        "!2B H 4B", msg_type, err_num, msg_id, num_colors_expected, 0, status, mode)

    for color in colors:
        r, g, b, l = color
        buf += struct.pack("!4B", r,g,b,l)

    return buf

def init_client_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    return sock

if __name__=="__main__":
    host, port = parse_cmdline_args()
    client_socket = init_client_socket()
    print(f"Sending request to {host}, {port}")
    req = parse_user_input_to_bytes()

    client_socket.sendto(req, (host, port))

    res, address = client_socket.recvfrom(4 * len(req))
