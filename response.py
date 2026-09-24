STATUS_TEXT = {200: "OK", 302: "Found", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found", 500: "Internal Server Error"}


class Response:
    content_type = "text/plain; charset=utf-8"

    def __init__(self, body="", status=200, headers=None, content_type=None):
        self.body = body
        self.status = status
        self.headers = headers or {}
        # internal list to hold multiple Set-Cookie values
        self._cookies = []
        if content_type is not None:
            self.content_type = content_type

    def to_bytes(self):
        if isinstance(self.body, bytes):
            body_bytes = self.body
        else:
            body_bytes = str(self.body).encode("utf-8")

        status_text = STATUS_TEXT.get(self.status, "")
        head_lines = [f"HTTP/1.1 {self.status} {status_text}"]

        head_lines.append(f"Content-Type: {self.content_type}")
        head_lines.append(f"Content-Length: {len(body_bytes)}")

        for k, v in self.headers.items():
            head_lines.append(f"{k}: {v}")

        # include any Set-Cookie headers collected via set_cookie()
        for cookie in getattr(self, "_cookies", []):
            head_lines.append(f"Set-Cookie: {cookie}")

        head_lines.append("Connection: close")

        head = "\r\n".join(head_lines) + "\r\n\r\n"
        return head.encode("utf-8") + body_bytes

    def set_cookie(self, name: str, value: str, *, path: str = "/", max_age: int = None, http_only: bool = False):
        """Add a Set-Cookie header value for this response.

        Example: `set_cookie('visits', '5', max_age=3600, http_only=True)`
        produces: `Set-Cookie: visits=5; Path=/; Max-Age=3600; HttpOnly`
        """
        if not hasattr(self, "_cookies") or self._cookies is None:
            self._cookies = []

        parts = [f"{name}={value}"]
        if path:
            parts.append(f"Path={path}")
        if max_age is not None:
            parts.append(f"Max-Age={int(max_age)}")
        if http_only:
            parts.append("HttpOnly")

        cookie_value = "; ".join(parts)
        self._cookies.append(cookie_value)

    def delete_cookie(self, name: str, *, path: str = "/"):
        """Mark a cookie for deletion by sending a Set-Cookie with empty value and Max-Age=0."""
        if not hasattr(self, "_cookies") or self._cookies is None:
            self._cookies = []
        parts = [f"{name}="]
        if path:
            parts.append(f"Path={path}")
        parts.append("Max-Age=0")
        cookie_value = "; ".join(parts)
        self._cookies.append(cookie_value)


class HTMLResponse(Response):
    content_type = "text/html; charset=utf-8"


class JSONResponse(Response):
    content_type = "application/json"

    def __init__(self, data, status=200):
        import json

        super().__init__(body=json.dumps(data), status=status, headers=None, content_type=self.content_type)


class RedirectResponse(Response):
    def __init__(self, location: str, status: int = 302, headers: dict = None):
        # empty body
        super().__init__(body="", status=status, headers=headers)
        # set Location header
        if self.headers is None:
            self.headers = {}
        self.headers.setdefault("Location", location)
