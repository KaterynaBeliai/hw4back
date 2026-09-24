from dataclasses import dataclass


@dataclass
class Request:
    method: str
    path: str
    headers: dict
    body: str
    query: dict = None
    cookies: dict = None

    def __post_init__(self):
        if self.query is None:
            self.query = {}
        if self.cookies is None:
            self.cookies = {}
