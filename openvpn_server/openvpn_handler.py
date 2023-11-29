#!/usr/bin/env python3
import configparser
import sys
sys.path.append("..") # Adds higher directory to python modules path.
from os import environ
import requests

import log

config = configparser.ConfigParser()
config_path = "../config.ini"
config.read(config_path)
HOST = config["SERVER"]["host"]
PORT = config["SERVER"]["port"]


def client_connect():
    cn = environ.get("common_name")
    if cn is None:
        return 1

    response = requests.get(f"http://{HOST}:{PORT}/ipv4/lock_any/{cn}/openvpn")
    if response.status_code < 200 or response.status_code > 299:
        log.error("openvpn", f"Couldn't lock any IP (ipv4): {response.status_code}")
        return 1
    response = response.json()
    ipv4 = response.get("ip")
    gateway = response.get("gateway")

    response = requests.get(f"http://{HOST}:{PORT}/ipv6/lock_any/{cn}/openvpn")
    if response.status_code < 200 or response.status_code > 299:
        log.error("openvpn", f"Couldn't lock any IP (ipv6): {response.status_code}")
        return 1
    ipv6 = response.json().get("ip")

    try:
        with open(sys.argv[1], "w+") as ovpn:
            print(f"push \"setenv-safe hcipv6   '{ipv6}'\"", file=ovpn)
            print(f"push \"setenv-safe hcipv4   '{ipv4}'\"", file=ovpn)
            print(f"push \"setenv-safe hcipv4hc '{gateway}'\"", file=ovpn)
            print(f"push \"setenv-safe ifconfig '{ipv4}")
    except Exception as e:
        print(e)
        return 1

    return 0


def client_disconnect():
    cn = environ.get("common_name")
    response = requests.put(f"http://{HOST}:{PORT}/ipv4/free_any/{cn}/openvpn")
    if response.status_code < 200 or response.status_code > 299:
        log.error("openvpn", f"Couldn't free IP (ipv4): {response.status_code}")
        return 1

    response = requests.put(f"http://{HOST}:{PORT}/ipv6/free_any/{cn}/openvpn")
    if response.status_code < 200 or response.status_code > 299:
        log.error("openvpn", f"Couldn't free IP (ipv6): {response.status_code}")
        return 1

    return 0


if __name__ == "__main__":
    if "script_type" in environ:
        script_type = environ.get("script_type")
        if "client-connect" == script_type:
            sys.exit(client_connect())
        if "client-disconnect" in script_type:
            sys.exit(client_disconnect())
