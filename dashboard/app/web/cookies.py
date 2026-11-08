def parse(header, name):
    for part in (header or "").split(";"):
        key, _, value = part.strip().partition("=")
        if key == name:
            return value

    return None


def session_cookie(name, token, max_age, secure):
    cookie = f"{name}={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}"
    if secure:
        cookie += "; Secure"

    return cookie


def expired_cookie(name):
    return f"{name}=; Path=/; Max-Age=0"
