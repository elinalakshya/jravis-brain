# app_lock.py — tiny PIN lock for your Flask app
import os
from flask import request, jsonify, make_response

APP_LOCK_PIN = os.getenv("APP_LOCK_PIN")  # set this in Replit Secrets

SAFE_PATHS = {
    "/", "/ping", "/health",  # uptime checks
}  # add others you want public

COOKIE_NAME = "va_lock"
HEADER_NAME = "X-App-Lock"

def _pin_ok(pin: str | None) -> bool:
    if not APP_LOCK_PIN:
        # No PIN configured -> unlocked
        return True
    return (pin or "") == APP_LOCK_PIN

def require_pin(app):
    @app.before_request
    def _check_pin():
        # allow safe paths without auth
        if request.path in SAFE_PATHS:
            return None

        # unlocked if no PIN configured
        if not APP_LOCK_PIN:
            return None

        # accept header, cookie, or query (?pin=xxx)
        pin = request.headers.get(HEADER_NAME) or request.cookies.get(COOKIE_NAME) or request.args.get("pin")
        if _pin_ok(pin):
            return None

        return jsonify({"ok": False, "error": "locked", "hint": f"Provide {HEADER_NAME} header or ?pin=..."}), 403

    @app.get("/unlock")
    def unlock():
        """Visit /unlock?pin=XXXX once to set a lock cookie."""
        pin = request.args.get("pin", "")
        if not _pin_ok(pin):
            return jsonify({"ok": False, "error": "invalid pin"}), 403
        resp = make_response(jsonify({"ok": True, "msg": "unlocked"}))
        # httpOnly cookie so JS can’t read it; path=/ to cover whole app
        resp.set_cookie(COOKIE_NAME, APP_LOCK_PIN, httponly=True, samesite="Lax")
        return resp

    @app.get("/lockout")
    def lockout():
        """Clear the cookie to lock the app again for this browser."""
        resp = make_response(jsonify({"ok": True, "msg": "locked out"}))
        resp.delete_cookie(COOKIE_NAME)
        return resp

    return app
