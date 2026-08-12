import contextlib
import socket
import threading
import typing


@contextlib.contextmanager
def stalled_urllib3_response() -> typing.Iterator[typing.Any]:
    import urllib3

    release = threading.Event()
    ready = threading.Event()
    server = socket.socket()
    server.bind(("127.0.0.1", 0))
    server.listen()
    port = server.getsockname()[1]

    def serve() -> None:
        connection, _address = server.accept()
        with connection:
            connection.recv(4096)
            connection.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 1000000\r\nConnection: close\r\n\r\nx")
            ready.set()
            release.wait(timeout=2)

    server_thread = threading.Thread(target=serve)
    server_thread.start()
    pool = urllib3.PoolManager(
        timeout=urllib3.Timeout(connect=1, read=1),
        retries=False,
    )
    response = pool.request(
        "GET",
        f"http://127.0.0.1:{port}/",
        preload_content=False,
    )
    assert ready.wait(timeout=1)
    try:
        yield response
    finally:
        release.set()
        response.close()
        pool.clear()
        server.close()
        server_thread.join(timeout=1)
