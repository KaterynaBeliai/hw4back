try:
    from .app import App
    from .server import HTTPServer
    from .templater import Templater
except Exception:
    # Allow running `python main.py` from inside the folder
    from app import App
    from server import HTTPServer
    from templater import Templater


def demo_render():

    t = Templater()
    html = t.render("demo", {"name": "John", "lang": "Python"})
    print("--- Rendered demo (hardcoded) ---")
    print(html)


if __name__ == "__main__":
    demo_render()
    app = App()
    HTTPServer(app).start()
