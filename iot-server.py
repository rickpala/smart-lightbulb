#!/usr/local/bin/python3
# iot-server.py

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

class LightBulb:
    """An IoT Light bulb which supports RGBL values."""
    # Status constants
    OFF = 0
    ON = 1

    # Mode constants
    STATIC = 0
    GRADIENT = 1

    def __init__(self, trigger_failure=False): 
        """By default, lightbulb is On, Static, and White at full brightness."""
        self.status = self.ON
        self.mode = self.STATIC
        self.colors = [(255,255,255,255)]
        self.failure = trigger_failure 
        self.req_ids = []
        self.error_code = 0

    def __str__(self):
        """Returns a Device Info string."""
        return "CS359 IoT RGB LightBulb"
        
    def print_current_state(self):
        """Prints a human-readable version of the current state of the lightbulb."""
        if self.status == 0:
            status = "OFF"
        else:
            status = "ON"

        if self.mode == 0:
            mode = "STATIC"
        else:
            mode = "GRADIENT"

        print(f"Lightbulb is {status} and {mode} at {self.colors}")

    def update(self, status, mode, colors):
        """Update the status, mode, and color(s) of the bulb."""
        if self.failure:
            print("Broken Lightbulb")
            return 

        self.status = status
        self.mode = mode
        self.colors = colors

    def headers_to_bytes(self):
        # - B Message Type
        # - B Err Num
        # - H Msg ID
        # - B N Colors
        # - x Pad
        # - B Status
        # - B Mode
        # - 4B * N RGBL Values (1B Each)
        buffer  = bytes()
        buffer += struct.pack(
            "!2B H 4B",
            1,
            self.error_code,
            self.req_ids[-1],
            len(self.colors),
            0,
            self.status,
            self.mode
            )
        
        for color in colors:
            r,g,b,l = color
            buffer += struct.pack("!4B", r,g,b,l)

        return buffer

    def dev_info_to_bytes(self):
        # - H Model Number
        # - H Device Version
        # - I String Length 
        # - S String with device Information

        # Append Model/Version Number, and Human-readable description
        desc = str(self) 
        buffer = self.headers_to_bytes() 
        buffer += struct.pack(f"!HHI {len(desc)}s", 1, 1, len(desc), desc.encode())
        return buffer

def parse_cmdline_args():
    if len(sys.argv) == 3:
        host = sys.argv[1]
        port = int(sys.argv[2])
    else:
        print("Bad cmd-line arguments.")
        quit()

    return (host, port)

def initialize_server_socket(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    print("The server is ready to receive on port:  " + str(port))
    return server_socket

if __name__=="__main__":
    (host, port) = parse_cmdline_args()
    server_socket = initialize_server_socket(host, port)
    lightbulb = LightBulb()

    # loop forever listening for incoming UDP messages
    while True:
        lightbulb.print_current_state()

        # recv message
        offset = 8
        buffer, client_addr = server_socket.recvfrom(1024)
        msg_type, err_num, msg_id, num_colors, err_num, status, mode \
            = struct.unpack("!2B H 4B", buffer[:offset])
        colors = []
        i = 0
        while len(colors) < num_colors:
            color = struct.unpack_from("!4B", buffer, offset + 4*i)
            colors.append(color)
            i += 1
        
        # interpret action
        lightbulb.req_ids.append(msg_id)
        device_info_req = (status == 0)

        if device_info_req:
            res = lightbulb.dev_info_to_bytes()
        else:
            status -= 1 # Device Info Request offsets On/Off values by 1
            lightbulb.update(status, mode, colors)
            res = lightbulb.headers_to_bytes()

        # send response
        server_socket.sendto(res, client_addr)
