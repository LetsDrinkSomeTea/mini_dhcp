#!/usr/bin/env python3
import requests
if __name__ == "__main__":
    base = "127.0.0.1:5000"
    requests.post(f"http://{base}/ipv4/195.201.45.84")
    requests.post(f"http://{base}/ipv4/195.201.252.250")
    requests.post(f"http://{base}/ipv6/2a01:4f8:c2c:a2ae::10")
    requests.post(f"http://{base}/ipv6/2a01:4f8:c2c:a2ae::15")