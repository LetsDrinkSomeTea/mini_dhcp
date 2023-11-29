import docker
import subprocess as sp
from os import environ

DOCKER_IMAGE = "testimage:2"


client = docker.from_env()
cn = environ.get("SUDO_USER", "")

try:
    container = client.containers.run(
        DOCKER_IMAGE,
        "/usr/bin/tmux",
        detach=True,
        stdin_open=True,
        auto_remove=True,
        tty=True,
        network_mode="none",
        shm_size="512M",
        volumes=[
            '/etc/tmux.conf:/etc/tmux.conf',
            f'/home/{cn}/.bash_history:/root/.bash_history',
            f'/home/{cn}/.bashrc:/root/.bashrc'
        ],
        cap_add=[
            "NET_ADMIN",
            "NET_RAW",
            "NET_BIND_SERVICE",
            "SYS_ADMIN",
            "SYS_PTRACE",
            "SYS_CHROOT"
        ]
    )
except Exception as e:
    print(f"Error: {cn} has no .bashrc or .bash_history")
    print(e)
    sys.exit(1)

