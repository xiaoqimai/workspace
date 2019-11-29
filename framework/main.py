from framework.conn import Conn
import tests

import argparse
import re
import os
import sys
import subprocess

def get_args():
    parser = argparse.ArgumentParser(description="pass through parameters")
    parser.add_argument("cmd", help="command to execute")
    parser.add_argument("-v", "--verbose", action="store_true", help="show execution steps")
    args = parser.parse_args()
    return args


def get_session(hostname, username, password, port=22, timeout=10):
    return Conn(hostname=hostname, username=username, password=password,port=port, timeout=timeout)




