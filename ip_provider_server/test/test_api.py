#!/usr/bin/env python
import unittest
import requests

BASE = "127.0.0.1:5000"


def populate_ips(n):
    for i in range(1, n+1):
        requests.post(f"http://{BASE}/ipv4/{i}")
        requests.post(f"http://{BASE}/ipv6/{i}")


def remove_ips():
    for i in requests.get(f"http://{BASE}/ipv4").json()["ipv4"]:
        requests.delete(f"http://{BASE}/ipv4/{i}")

    for i in requests.get(f"http://{BASE}/ipv6").json()["ipv6"]:
        requests.delete(f"http://{BASE}/ipv6/{i}")


class MyTestCase(unittest.TestCase):
    base = "127.0.0.1:5000"

    def test_insert_delete(self):
        response = requests.post(f"http://{self.base}/ipv4/1")
        self.assertEqual(response.status_code, 201)
        response = requests.post(f"http://{self.base}/ipv4/1")
        self.assertEqual(response.status_code, 409)
        response = requests.delete(f"http://{self.base}/ipv4/1")
        self.assertEqual(response.status_code, 200)

    def test_get_all(self):
        populate_ips(10)
        response = requests.get(f"http://{self.base}/ipv4")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ipv4"]), 10)
        remove_ips()

    def test_lock_free_any(self):
        populate_ips(10)
        response = requests.get(f"http://{self.base}/ipv4/lock_any/test/openvpn")
        self.assertEqual(response.status_code, 200)
        response = requests.get(f"http://{self.base}/ipv4/used")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()["ipv4"]))
        response = requests.put(f"http://{self.base}/ipv4/free_any/test/openvpn")
        self.assertEqual(response.status_code, 200)
        remove_ips()

    def test_get_available(self):
        response = requests.get(f"http://{self.base}/ipv4/available")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ipv4"]), 0)
        populate_ips(10)
        response = requests.get(f"http://{self.base}/ipv4/available")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ipv4"]), 10)
        remove_ips()

    def test_get_used(self):
        response = requests.get(f"http://{self.base}/ipv4/used")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ipv4"]), 0)
        populate_ips(10)
        response = requests.get(f"http://{self.base}/ipv4/used")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ipv4"]), 0)
        response = requests.get(f"http://{self.base}/ipv4/lock_any/test/openvpn")
        used_ip = response.json()["ip"]
        self.assertEqual(response.status_code, 200)
        response = requests.get(f"http://{self.base}/ipv4/used")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["ipv4"]), 1)
        self.assertEqual(response.json()["ipv4"][0], used_ip)
        response = requests.put(f"http://{self.base}/ipv4/free_any/test/openvpn")
        self.assertEqual(200, response.status_code)
        remove_ips()

    def test_double_lock(self):
        populate_ips(10)
        response = requests.put(f"http://{self.base}/ipv4/lock/1/test/openvpn")
        self.assertEqual(response.status_code, 200)
        response = requests.put(f"http://{self.base}/ipv4/lock/1/test/openvpn")
        self.assertEqual(response.status_code, 423)
        response = requests.get(f"http://{self.base}/ipv4/used")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(1, len(response.json()["ipv4"]))
        response = requests.put(f"http://{self.base}/ipv4/free/1/test")
        self.assertEqual(response.status_code, 200)
        remove_ips()

    def test_free_by_diffrent_user(self):
        populate_ips(5)
        response = requests.put(f"http://{self.base}/ipv4/lock/1/test/docker")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ip"], "1")
        response = requests.put(f"http://{self.base}/ipv4/free/1/test2")
        self.assertEqual(response.status_code, 423)
        response = requests.get(f"http://{self.base}/ipv4/used")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ipv4"][0], "1")
        response = requests.put(f"http://{self.base}/ipv4/free/1/test")
        self.assertEqual(response.status_code, 200)
        remove_ips()


if __name__ == '__main__':
    unittest.main()
