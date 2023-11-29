# Use the base image you want to build upon
FROM kalilinux/kali-rolling

# Install tmux
RUN apt-get update && \
    apt-get install -y tmux && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && \
    apt-get install -y iproute2

# Set the default command when a container is run
CMD ["tmux"]
