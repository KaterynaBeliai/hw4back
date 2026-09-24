import os


class Templater:
    def __init__(self, pages_dir=None):
        if pages_dir is None:
            base = os.path.dirname(__file__)
            pages_dir = os.path.join(base, "pages")
        self.pages_dir = pages_dir

    def read(self, filename):
        path = os.path.join(self.pages_dir, filename)
        if not os.path.isfile(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    def render(self, name, params=None):
        content = self.read(f"{name}.html")
        if content is None:
            return None

        page = (self.read("header.html") or "") + content + (self.read("footer.html") or "")

        if params:
            for key, value in params.items():
                page = page.replace(f"{{{key}}}", str(value))

        return page
