import os

try:
    from .response import HTMLResponse, RedirectResponse, JSONResponse
    from .templater import Templater
    from .http_parser import parse_query_string
    from .users import check_password, USERS
    from .sessions import create_session, get_session, delete_session
    from .tokens import make_token, verify_token
except Exception:
    from response import HTMLResponse, RedirectResponse, JSONResponse
    from templater import Templater
    from http_parser import parse_query_string
    from users import check_password, USERS
    from sessions import create_session, get_session, delete_session
    from tokens import make_token, verify_token


class App:
    def __init__(self, pages_dir=None):
        self.templater = Templater(pages_dir)

    def login_form(self, error=""):
        html = self.templater.render("login", {"error": error})
        return HTMLResponse(html)

    def handle(self, request):
        path = request.path
        if ".." in path:
            return HTMLResponse("Not Found", status=404)

        # special route to reset visits cookie and redirect to index
        if path == "/reset":
            resp = RedirectResponse("/")
            resp.delete_cookie("visits")
            return resp

        # logout (delete session)
        if path == "/logout":
            # delete server-side session if present
            sid = (request.cookies or {}).get("session_id")
            if sid:
                delete_session(sid)
            resp = RedirectResponse("/")
            # try delete session cookie and visits cookie
            resp.delete_cookie("session_id")
            resp.delete_cookie("visits")
            return resp

        # login form and submission
        if path == "/login":
            # POST must be handled before GET for PRG
            if request.method.upper() == "POST":
                # parse form-encoded body
                form = parse_query_string(request.body or "")
                username = form.get("username") or ""
                password = form.get("password") or ""
                use_cookie = form.get("insecure") == "1"

                # check credentials via users.check_password
                if not check_password(username, password):
                    return self.login_form(error="Login failed")

                # demo role: 'admin' username gets admin role
                role = "admin" if username == "admin" else "user"

                if use_cookie:
                    # insecure: store user data directly in cookies
                    resp = RedirectResponse("/profile")
                    resp.set_cookie("user", username)
                    resp.set_cookie("role", role)
                    resp.set_cookie("email", USERS.get(username, {}).get("email"), max_age=3600)
                    return resp

                # secure: create server-side session and set HttpOnly cookie
                sid = create_session({"user": username, "role": role, "email": USERS.get(username, {}).get("email")})
                resp = RedirectResponse("/profile")
                resp.set_cookie("session_id", sid, max_age=3600, http_only=True)
                return resp

            # GET -> show form
            if request.method.upper() == "GET":
                return self.login_form()

        # profile view
        if path == "/profile":
            # get session from session store
            sid = (request.cookies or {}).get("session_id")
            session = get_session(sid)
            if session is None:
                # fallback to insecure cookies for Task 1 compatibility
                user = (request.cookies or {}).get("user")
                role = (request.cookies or {}).get("role")
                email = (request.cookies or {}).get("email")
                if not user:
                    return RedirectResponse("/login")
                html = self.templater.render("profile", params={"user": user, "role": role, "email": email})
                return HTMLResponse(html)

            # render from session
            html = self.templater.render("profile", params={"user": session.get("user"), "role": session.get("role"), "email": session.get("email")})
            return HTMLResponse(html)

        # API: token-based login (returns JSON with token)
        if path == "/api/login":
            if request.method.upper() == "POST":
                form = parse_query_string(request.body or "")
                username = form.get("username") or ""
                password = form.get("password") or ""
                if not check_password(username, password):
                    return JSONResponse({"error": "invalid_credentials"}, status=401)
                # build token payload
                role = "admin" if username == "admin" else "user"
                # make_token expects (username, role)
                token = make_token(username, role)
                return JSONResponse({"token": token})
            return JSONResponse({"error": "method_not_allowed"}, status=401)

        # API: token-protected profile
        if path == "/api/profile":
            # look for Authorization: Bearer <token>
            auth = (request.headers or {}).get("authorization")
            if not auth or not auth.lower().startswith("bearer "):
                return JSONResponse({"error": "missing_authorization"}, status=401)
            token = auth.split(None, 1)[1]
            payload = verify_token(token)
            if payload is None:
                return JSONResponse({"error": "invalid_token"}, status=401)
            # tokens.py uses 'username' key
            return JSONResponse({"user": payload.get("username"), "role": payload.get("role")})

        # admin page
        if path == "/admin":
            sid = (request.cookies or {}).get("session_id")
            session = get_session(sid)
            role = None
            if session is not None:
                role = session.get("role")
            else:
                role = (request.cookies or {}).get("role")

            if sid is None and role is None:
                return RedirectResponse("/login")

            if role != "admin":
                return HTMLResponse("403 Forbidden", status=403)

            return HTMLResponse("Welcome to admin area")

        if path == "/":
            name = "index"
        else:
            name = path.lstrip("/")

        # merge query params and other template params
        params = dict(request.query or {})

        # if this is the index page, use a cookie-based visits counter
        if path == "/":
            visits = 0
            visits_raw = (request.cookies or {}).get("visits")
            if isinstance(visits_raw, str) and visits_raw.isdigit():
                visits = int(visits_raw)
            else:
                visits = 0
            visits = visits + 1
            params["visits"] = visits

        html = self.templater.render(name, params=params)
        if html is None:
            return HTMLResponse("Not Found", status=404)

        response = HTMLResponse(html)
        # set updated visits cookie for index page
        if path == "/":
            response.set_cookie("visits", str(params.get("visits", "0")))

        return response
