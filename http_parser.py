try:
    from .request import Request
except Exception:
    from request import Request


def split_target(target):
    """Return (path, query_string).

    "/hello?name=John" -> ("/hello", "name=John"); no ? -> (target, "").
    """
    if "?" not in target:
        return target, ""
    before, _, after = target.partition("?")
    return before, after


def parse_query_string(text):
    """Parse name=John&lang=Python -> {'name':'John','lang':'Python'}.

    Split on '&', then each pair on '=' with maxsplit=1. Skip pairs without '='.
    """
    if not text:
        return {}

    def pct_decode(s: str) -> str:
        # simple percent-decoder, handles %HH and plus -> space
        res = []
        i = 0
        n = len(s)
        while i < n:
            ch = s[i]
            if ch == "%" and i + 2 < n:
                hexpart = s[i+1:i+3]
                try:
                    code = int(hexpart, 16)
                    res.append(chr(code))
                    i += 3
                    continue
                except ValueError:
                    # if not valid hex, keep literal '%'
                    res.append("%")
                    i += 1
                    continue
            if ch == "+":
                res.append(" ")
            else:
                res.append(ch)
            i += 1
        return "".join(res)

    result = {}
    for part in text.split("&"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        result[pct_decode(k)] = pct_decode(v)
    return result


def parse_cookies(text: str):
    """Parse 'visits=3; theme=dark' -> {'visits':'3', 'theme':'dark'}."""
    if not text:
        return {}
    result = {}
    # cookies are separated by ';'
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            # skip malformed entries
            continue
        k, v = part.split("=", 1)
        result[k.strip()] = v.strip()
    return result


def parse_request(text: str) -> Request:
    head, sep, body = text.partition("\r\n\r\n")
    lines = head.split("\r\n")
    if not lines:
        return Request(method="", path="", headers={}, body="", query={})

    request_line = lines[0]
    method, target, version = parse_request_line(request_line)
    path, q = split_target(target)
    query = parse_query_string(q)

    headers = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            continue
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()

    # parse cookies from headers (Cookie header is optional)
    cookie_header = headers.get("cookie", "")
    cookies = parse_cookies(cookie_header)

    return Request(method=method, path=path, headers=headers, body=body, query=query, cookies=cookies)


def parse_request_line(line: str):
    parts = line.split(" ")
    if len(parts) != 3:
        return "", "", ""
    return parts[0], parts[1], parts[2]
