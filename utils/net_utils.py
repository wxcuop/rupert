import socket
import errno


def connect_tcpip_transport(remote_host: str, remote_port: str) -> socket.socket:
    """Establishes a TCP connection to the given host and port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.connect((remote_host, int(remote_port)))
        return sock
    except socket.error as e:
        raise Exception(f"connect_tcpip_transport: {e}")


def set_fd_nonblocking(sock: socket.socket):
    """Sets the given socket to non-blocking mode."""
    sock.setblocking(False)


def listen_tcpip_transport(local_port: int, is_fd_non_blocking: bool) -> socket.socket:
    """Creates a listening TCP socket on the given port."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        sock.bind(("", local_port))
        sock.listen(5)

        if is_fd_non_blocking:
            set_fd_nonblocking(sock)

        return sock
    except socket.error as e:
        raise Exception(f"listen_tcpip_transport: {e}")


def accept_tcpip_transport(listen_sock: socket.socket) -> socket.socket:
    """Accepts an incoming TCP connection."""
    try:
        client_sock, client_addr = listen_sock.accept()
        print(f"Accepted new connection from {client_addr}")
        return client_sock
    except socket.error as e:
        if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
            return None
        raise Exception(f"accept_tcpip_transport: {e}")
