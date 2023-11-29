#!/usr/bin/env python3
import requests


def main():
    base = "127.0.0.1:5000"

    while True:
        method = input("Enter method (get, post, put, del, quit): ")

        if method == "quit":
            break

        route = input("Enter route: ")

        if method == "get":
            response = requests.get(f"http://{base}/{route}")
            print(response.status_code)
            print(response.json())
        elif method == "put":
            response = requests.put(f"http://{base}/{route}")
            print(response.status_code)
            print(response.json())
        elif method == "post":
            response = requests.post(f"http://{base}/{route}")
            print(response.status_code)
            print(response.json())
        elif method == "del":
            response = requests.delete(f"http://{base}/{route}")
            print(response.status_code)
            print(response.json())
        else:
            print("Unknown method")


if __name__ == '__main__':
    main()
