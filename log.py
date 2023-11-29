from datetime import time, datetime

RED = "[91m"
GREEN = "[92m"
YELLOW = "[93m"
BLUE = "[94m"
ORANGE = "[33m"
GREY = "[90m"


def error(script, msg, color=ORANGE):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in red
    print(f"\033{color}[{script}] {time_str} [ERR]: {msg}\033[0m")


def info(script, msg, color=BLUE):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in blue
    print(f"\033{color}[{script}] {time_str} [INF]: {msg}\033[0m")


def warn(script, msg, color=YELLOW):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in yellow
    print(f"\033{color}[{script}] {time_str} [WRN]: {msg}\033[0m")


def connect(script, device, ip, gateway, used_for, color=GREEN):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in green
    print(f"\033{color}[{script}] {time_str} [CON]: {device} IP: {ip} GW: {gateway} Purpose: {used_for} \033[0m")


def disconnect(script, device, ip, color=RED):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print in orange
    print(f"\033{color}[{script}] {time_str} [DIS]: {device} IP: {ip}\033[0m")
