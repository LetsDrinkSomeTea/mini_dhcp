import os.path
import sys
from datetime import time, datetime

RED = "[91m"
GREEN = "[92m"
YELLOW = "[93m"
BLUE = "[94m"
ORANGE = "[33m"
GREY = "[90m"

LOG_PATH = "log.txt"

VERBOSE = True


def error(script, msg, color=ORANGE):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in red
    _print_and_log(f"[{script}] {time_str} [ERR]: {msg}", color=color)


def info(script, msg, color=BLUE):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in blue
    _print_and_log(f"[{script}] {time_str} [INF]: {msg}", color=color)


def warn(script, msg, color=YELLOW):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in yellow
    _print_and_log(f"[{script}] {time_str} [WRN]: {msg}", color=color)


def connect(script, device, ip, gateway, used_for, color=GREEN):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in green
    _print_and_log(f"[{script}] {time_str} [CON]: {device} IP: {ip} GW: {gateway} Purpose: {used_for}", color=color)


def disconnect(script, device, ip, color=RED):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _print_and_log(f"[{script}] {time_str} [DIS]: {device} IP: {ip}", color=color)


def _print_and_log(log_string, color):
    with open(LOG_PATH, "a+") as log_file:
        log_file.write(log_string + "\n")
    if VERBOSE:
        print(f"\033{color}{log_string}\033[0m")
        