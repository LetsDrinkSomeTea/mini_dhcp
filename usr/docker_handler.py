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
DOCKER_IMAGE = config["DOCKER"]["image"]


def get_ip_from_user(user, docker_id):
    response = requests.get(f"http://{HOST}:{PORT}/ipv4/available").json()
    print("Please select an IP address from the list below (0) for default:")
    for n, ip in enumerate(response.get("ipv4"), start=1):
        print(f"[{n}]: {ip}")
    ip = input("IP: ")
    if ip == "0" or ip == "":
        response = requests.get(f"http://{HOST}:{PORT}/ipv4/lock_any/{user}/{docker_id}")
    elif ip.isdigit() and 0 < int(ip) <= len(response.get("ipv4")):
        selected_ip = response.get("ipv4")[int(ip) - 1]
        response = requests.put(f"http://{HOST}:{PORT}/ipv4/lock/{selected_ip}/{user}/{docker_id}")
    else:
        return get_ip_from_user(user, docker_id)

    if 200 <= response.status_code < 300:
        return response.json()
    else:
        log.error("docker_handler", f"Couldn't lock IP: {response.status_code}")
        sys.exit(1)


def create(cn):
    import docker
    import subprocess as sp

    client = docker.from_env()

    sysctl_setting = {'net.ipv6.conf.all.disable_ipv6': '0'}

    try:
        container = client.containers.run(DOCKER_IMAGE,
                                          "/usr/bin/tmux",
                                          detach=True,
                                          stdin_open=True,
                                          auto_remove=True,
                                          tty=True,
                                          network_mode="none",
                                          shm_size="512M",
                                          volumes=['/etc/tmux.conf:/etc/tmux.conf',
                                                   f"/home/{cn}/.bash_history:/root/.bash_history",
                                                   f"/home/{cn}/.bashrc:/root/.bashrc"],
                                          cap_add=["NET_ADMIN", "NET_RAW", "NET_BIND_SERVICE", "SYS_ADMIN", "SYS_PTRACE", "SYS_CHROOT"],
                                          sysctls=sysctl_setting
                                          )
    except Exception as e:
        print(e)
        log.error("docker_handler", f"{cn} probably dont has .bash_history or .bashrc")
        return 1

    response = get_ip_from_user(cn, container.id)
    ipv4 = response.get("ip")
    gateway = response.get("gateway")

    response = requests.get(f"http://{HOST}:{PORT}/ipv6/lock_any/{cn}/{container.id}")
    if response.status_code < 200 or response.status_code > 299:
        log.error("docker_handler", f"Couldn't lock any IP (ipv6): {response.status_code}")
        return 1
    ipv6 = response.json().get("ip")
    ipv6_gateway = response.json().get("gateway")

    ip_bin = "/sbin/ip"
    br_bin = "/sbin/brctl"
    ns_bin = "/usr/bin/nsenter"

    container.reload()
    cpid = str(container.attrs["State"]["Pid"])


    container_sid = container.id[0:4]
    interface_int = f"{container_sid}-int"
    interface_ext = f"{container_sid}-ext"
    interface_int_v6 = f"{container_sid}-int-v6"
    interface_ext_v6 = f"{container_sid}-ext-v6"

    sp.run([ip_bin, "link", "add", interface_int, "type", "veth", "peer", "name", interface_ext])
    sp.run([br_bin, "addif", "br0", interface_ext])
    sp.run([ip_bin, "link", "set", interface_ext, "up"])
    sp.run([ip_bin, "link", "set", "netns", cpid, "dev", interface_int])
    sp.run([ns_bin, "-t", cpid, "-n", ip_bin, "addr", "add", f"{ipv4}/32", "peer", gateway, "dev", interface_int])
    sp.run([ns_bin, "-t", cpid, "-n", ip_bin, "link", "set", interface_int, "up"])
    sp.run([ns_bin, "-t", cpid, "-n", ip_bin, "route", "add", "default", "via", gateway, "dev", interface_int])

    sp.run([ip_bin, "-6", "link", "add", interface_int_v6, "type", "veth", "peer", "name", interface_ext_v6])
#    sp.run([ip_bin, "-6", "link", "set", interface_ext_v6, "master", "br0"])
    sp.run([br_bin, "addif", "br0", interface_ext_v6])
    sp.run([ip_bin, "-6", "link", "set", interface_ext_v6, "up"])
    sp.run([ip_bin, "-6", "link", "set", "netns", cpid, "dev", interface_int_v6])

    sp.run([ns_bin, "-t", cpid, "-n", ip_bin, "-6", "addr", "add", f"{ipv6}/64", "dev", interface_int_v6])  # Use the retrieved IPv6 address
    sp.run([ns_bin, "-t", cpid, "-n", ip_bin, "-6", "link", "set", interface_int_v6, "up"])
    sp.run([ns_bin, "-t", cpid, "-n", ip_bin, "-6", "route", "add", "::/0", "via", ipv6_gateway, "dev", interface_int_v6])

    print(container.id)
    return 0


def resume(cn, ip, ipv6, docker_id):
    import docker

    client = docker.from_env()
    container = next((container for container in client.containers.list() if container.id == docker_id), None)

    if container and container.status == "running":
        print(container.id)
        return 1
    else:
        response = requests.put(f"http://{HOST}:{PORT}/ipv4/free/{ip}/{cn}")
        response_v6 = requests.put(f"http://{HOST}:{PORT}/ipv6/free/{ipv6}/{cn}")
        return 200 <= response.status_code < 300 and 200 <= response_v6.status_code < 300


def manage_docker():
    cn = environ.get("SUDO_USER", "")

    if len(cn) == 0:
        print("No sudo, no sandwich")
        return 1

    # get ipv4/used/{user}
    response = requests.get(f"http://{HOST}:{PORT}/ipv4/used/{cn}").json()
    list_of_ips = response.get("ipv4")
    ip = None
    for item in list_of_ips:
        ip = item.get("ip")
        used_for = item.get("used_for")
        if used_for != "openvpn":
            break

    response = requests.get(f"http://{HOST}:{PORT}/ipv6/used/{cn}").json()
    list_of_ips = response.get("ipv6")
    ipv6 = None
    for item in list_of_ips:
        ipv6 = item.get("ip")
        used_for = item.get("used_for")
        if used_for != "openvpn":
            break

    if not ip and not ipv6:
        return create(cn)

    return resume(cn, ip, ipv6, used_for)


if __name__ == "__main__":
    manage_docker()
