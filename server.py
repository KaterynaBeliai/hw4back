import os
import socket

try:
    from .http_parser import parse_request
    from .response import HTMLResponse, Response
except Exception:
    from http_parser import parse_request
    from response import HTMLResponse, Response

CONTENT_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".png": "image/png",
    ".svg": "image/svg+xml",
}


class HTTPServer:
    def __init__(self, app, host="0.0.0.0", port=8080, static_dir=None):
        self.app = app
        self.host = host
        self.port = port
        if static_dir is None:
            base = os.path.dirname(__file__)
            static_dir = os.path.join(base, "static")
        self.static_dir = static_dir

    def _serve_static(self, path):
        # path begins with /static/
        if ".." in path:
            return HTMLResponse("Not Found", status=404)

        rel = path[len("/static/"):]
        filename = os.path.join(self.static_dir, rel)
        if not os.path.isfile(filename):
            return HTMLResponse("Not Found", status=404)

        ext = os.path.splitext(filename)[1].lower()
        ctype = CONTENT_TYPES.get(ext, "application/octet-stream")

        if ext in [".png", ".svg"]:
            with open(filename, "rb") as f:
                data = f.read()
            return Response(body=data, status=200, content_type=ctype)
        else:
            with open(filename, "r", encoding="utf-8") as f:
                text = f.read()
            return Response(body=text, status=200, content_type=ctype)

    def start(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen()
            print(f"Listening on http://{self.host}:{self.port}")

            while True:
                client, addr = s.accept()
                with client:
                    try:
                        data = b""

                        # read until headers end
                        while b"\r\n\r\n" not in data:
                            chunk = client.recv(4096)
                            if not chunk:
                                break
                            data += chunk

                        head, sep, body = data.partition(b"\r\n\r\n")
                        header_text = head.decode("utf-8", errors="replace")
                        header_lines = header_text.split("\r\n")
                        print(f"[DEBUG] Raw request head:\n{header_text}")
                        # parse headers into dict
                        headers = {}
                        for line in header_lines[1:]:
                            if ":" in line:
                                n, v = line.split(":", 1)
                                headers[n.strip().lower()] = v.strip()
                        print(f"[DEBUG] Parsed headers: {headers}")

                        content_length = int(headers.get("content-length", "0"))
                        # read remaining body bytes if any
                        body_bytes = body
                        while len(body_bytes) < content_length:
                            chunk = client.recv(4096)
                            if not chunk:
                                break
                            body_bytes += chunk

                        text = (head + b"\r\n\r\n" + body_bytes).decode("utf-8", errors="replace")
                        request = parse_request(text)
                        # diagnostic: log parsed request path/method
                        print(f"[DEBUG] Parsed request: method={request.method!r}, path={request.path!r}")

                        if request.path.startswith("/static/"):
                            response = self._serve_static(request.path)
                        else:
                            response = self.app.handle(request)
                    except Exception as exc:
                        body = f"Internal Server Error: {exc}"
                        response = HTMLResponse(body, status=500)

                    client.sendall(response.to_bytes())
