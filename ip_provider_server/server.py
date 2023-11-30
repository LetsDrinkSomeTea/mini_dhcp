#!/usr/bin/env python3
import sys
from flask import Flask, jsonify
import ip_provider as ipp
import os
import logging
import configparser
import argparse
sys.path.append("..")  # Adds higher directory to python modules path.
import log
logger = logging.getLogger('werkzeug')
logger.setLevel(logging.ERROR)


ipp.IPProvider.DB_PATH = "../ips.sqlite"

argparser = argparse.ArgumentParser()
argparser.add_argument("-c", "--clean", action="store_true", help="Clean the database")
argparser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")
args = argparser.parse_args()

config = configparser.ConfigParser()
config_path = "../config.ini"
config.read(config_path)


if args.clean:
    if os.path.exists(ipp.IPProvider.DB_PATH):
        os.remove(ipp.IPProvider.DB_PATH)
    if os.path.exists(log.LOG_PATH):
        os.remove(log.LOG_PATH)
if args.verbose:
    log.VERBOSE = True
else:
    log.VERBOSE = False

if not os.path.exists(ipp.IPProvider.DB_PATH):
    ipp.IPProvider.create_db()

ipv4_provider = ipp.IPv4Provider(ip_gateway=config["GATEWAYS"]["ipv4"])
ipv6_provider = ipp.IPv6Provider(ip_gateway=config["GATEWAYS"]["ipv6"])

app = Flask(__name__)


def determine_ip_provider(ip_version):
    if ip_version == "ipv4":
        return ipv4_provider
    elif ip_version == "ipv6":
        return ipv6_provider
    else:
        log.error("server", f"Invalid IP version: {ip_version}")
        return None


@app.get("/<ip_version>")
def get_ips(ip_version):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400
    ips = ip_provider.get_all_ips()
    log.info("server", f"Get all IPs ({ip_version})")
    return {ip_version: ips}, 200


@app.get("/<ip_version>/available")
def get_available_ip(ip_version):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400
    available_ips = ip_provider.get_available_ips()
    log.info("server", f"Get available IPs ({ip_version})")
    return {ip_version: available_ips}, 200


@app.get("/<ip_version>/used")
def get_used_ip(ip_version):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400
    used_ips = ip_provider.get_used_ips()
    log.info("server", f"Get used IPs ({ip_version})")
    return {ip_version: used_ips}, 200


@app.get("/<ip_version>/used/<user>")
def get_used_ip_by_user(ip_version, user):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400
    used_ips = ip_provider.get_used_ips_by_user(user)
    log.info("server", f"Get used IPs ({ip_version}) by {user}")
    return {ip_version: used_ips}, 200


@app.put("/<ip_version>/lock/<ip>/<user>/<used_for>")
def lock_ip(ip_version, ip, user, used_for):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400
    if ip not in ip_provider.get_all_ips():
        log.warn("server", f"IP ({ip_version}): {ip} not found")
        return ip, 404

    if ip_provider.lock_ip_address(ip, user, used_for):
        log.connect("server", user, ip, gateway=ip_provider.IP_GATEWAY, used_for=used_for)
        return jsonify(ip=ip, gateway=ip_provider.IP_GATEWAY)
    else:
        log.error("server", f"IP ({ip_version}): {ip} is not free")
        return ip, 423


@app.get("/<ip_version>/lock_any/<user>/<used_for>")
def lock_any_ip(ip_version, user, used_for):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400

    ip = ip_provider.lock_any_ip_address(user, used_for)
    if ip:
        log.connect("server", user, ip, gateway=ip_provider.IP_GATEWAY, used_for=used_for)
        return jsonify(ip=ip, gateway=ip_provider.IP_GATEWAY)
    else:
        log.error("server", f"IP ({ip_version}): No free IPs")
        return "Failed", 423


# get the user from the body of the request
@app.put("/<ip_version>/free/<ip>/<user>")
def free_ip(ip_version, ip, user):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400
    if ip not in ip_provider.get_all_ips():
        log.warn("server", f"IP ({ip_version}): {ip} not found")
        return ip, 404

    if ip_provider.free_ip_address(ip, user):
        log.disconnect("server", user, ip)
        return ip, 200
    else:
        log.error("server", f"IP ({ip_version}): {ip} is not locked by {user}")
        return ip, 423


@app.put("/<ip_version>/free_any/<user>/<used_for>")
def free_any_ip(ip_version, user, used_for):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 400

    ip = ip_provider.free_any_ip_address(user, used_for)
    if ip:
        log.disconnect("server", user, ip)
        return ip, 200
    else:
        log.error("server", f"IP ({ip_version}): Not locked by {user} for {used_for}")
        return "Failed", 423


@app.post("/<ip_version>/<ip>")
def add_ip(ip_version, ip):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 404
    if ip_provider.add_ip(ip):
        log.info("server", f"Added IP ({ip_version}): {ip}", color=log.GREY)
        return ip, 201
    else:
        log.warn("server", f"IP ({ip_version}): {ip} already exists")
        return ip, 409


@app.delete("/<ip_version>/<ip>")
def delete_ip(ip_version, ip):
    ip_provider = determine_ip_provider(ip_version)
    if not ip_provider:
        return ip_version, 404

    if ip not in ip_provider.get_all_ips():
        log.warn("server", f"IP ({ip_version}): {ip} not found")
        return ip, 404

    if ip_provider.delete_ip(ip):
        log.info("server", f"Deleted IP ({ip_version}): {ip}", color=log.GREY)
        return ip, 200
    else:
        log.error("server", f"IP ({ip_version}): {ip} is not free")
        return ip, 423


app.run(host=config["SERVER"]["host"], port=config["SERVER"]["port"])
