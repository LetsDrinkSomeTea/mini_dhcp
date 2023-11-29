#!/usr/bin/env python3
import configparser

import requests
if __name__ == "__main__":
    config = configparser.ConfigParser()
    config_path = "../../config.ini"
    config.read(config_path)
    HOST = config["SERVER"]["host"]
    PORT = config["SERVER"]["port"]

    base = f"{HOST}:{PORT}"
    requests.post(f"http://{base}/ipv4/195.201.45.84")
    requests.post(f"http://{base}/ipv4/195.201.252.250")
    requests.post(f"http://{base}/ipv6/2a01:4f8:c2c:a2ae::10")
    requests.post(f"http://{base}/ipv6/2a01:4f8:c2c:a2ae::15")