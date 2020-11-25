#!/usr/local/bin/python3
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
def dev_info_req_to_bytes(msg_id):
    return struct.pack("!2B H 4B", 0, 0, msg_id, 0, 0, 0, 0) 

def turn_off_req_to_bytes(msg_id):
    return struct.pack("!2B H 4B", 0, 0, msg_id, 0, 0, 1, 0) 

def parse_cmdline_args():
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        print("Bad cmd-line arguments.")
        quit()

    return host, port

def init_client_socket():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)
    return sock

def build_req_str(host, port, msg_id, num_colors_expected, status, mode, colors):
    req_str = ""
    req_str += f"Sending request to {host}, {port}\n"
    req_str += f"Message Type: 0\n"
    req_str += f"Message ID: {msg_id}\n"
    req_str += f"Number of Colors: {num_colors_expected}\n"
    req_str += f"Status: {status}\n"
    req_str += f"Mode: {mode}\n"
    for i, color in enumerate(colors):
        req_str += f"Color {i} RGBL: {str(color)}\n"

    return req_str

def build_res_str(msg_type, err_num, msg_id, num_colors, pad, status, mode):
    res_str = ""
    res_str += f"Error Number: {err_num}\n"
    res_str += f"Message Type: {msg_type}\n"
    res_str += f"Message ID: {msg_id}\n"
    res_str += f"Number of colors: {num_colors}\n"
    res_str += f"Status: {status}\n"
    res_str += f"Mode: {mode}\n"
    return res_str

if __name__=="__main__":
    host, port = parse_cmdline_args()
    client_socket = init_client_socket()

    msg_type = 0
    err_num = 0
    num_colors_expected = 0
    mode = 0
    colors = []
    msg_id = random.randint(0, 2**16)

    # Ask for status 
    status = int(input("Status [0 Info Request, 1 Off, 2 On]: "))
    is_device_info_req = (status == 0)
    is_turn_off_req = (status == 1)
    is_turn_on_req = (status == 2)

    if is_device_info_req:
        req = dev_info_req_to_bytes(msg_id)
    elif is_turn_off_req:
        req = turn_off_req_to_bytes(msg_id)
    elif is_turn_on_req:
        # Ask user for mode 
        mode = int(input("Mode [0 Static, 1 Gradient]: "))
        static_mode = (mode == 0) 
        gradient_mode = (mode == 1)
        if static_mode:
            num_colors_expected = 1
        elif gradient_mode:
            num_colors_expected = 2
        else:
            print("Mode Error")
            quit()

        colors = []
        while len(colors) < num_colors_expected:
            color = input(f"Color {len(colors)} (R,G,B,L): ")
            color_tpl = eval(color)
            colors.append(color_tpl)        

        # Pack request 
        req  = bytes()
        req += struct.pack(
            "!2B H 4B", msg_type, err_num, msg_id, num_colors_expected, 0, status, mode)
        for color in colors:
            r, g, b, l = color
            req += struct.pack("!4B", r,g,b,l)
    else:
        print("Status Error")
        quit()

    # Print the request data
    req_str = build_req_str(host, port, msg_id, num_colors_expected, status, mode, colors)
    print(req_str)
    
    client_socket.sendto(req, (host, port))

    # Unpack and receive response 
    buffer, address = client_socket.recvfrom(4 * len(req))
    offset = 8
    print(f"Received response from {address}")
    print(f"Buffer size: {len(buffer)}")
    fmt_string = "!BB H BBBB"
    msg_type, err_num, msg_id, num_colors, pad, status, mode = \
        struct.unpack(fmt_string, buffer[:offset]) 
    res_str = build_res_str(msg_type, err_num, msg_id, num_colors, pad, status, mode)

    if not is_device_info_req:
        offset = 8
        colors = []
        i = 0
        while len(colors) < num_colors:
            color = struct.unpack_from("!4B", buffer, offset + 4*i)
            colors.append(color)
            res_str += f"Color {i} RGBL: {color}\n"
            i += 1
    print(res_str)
