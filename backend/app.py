import logging
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import PurePosixPath

from flask import Flask, abort, jsonify, request, send_from_directory

import config
import sheets
import validators

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("form-backend")

app = Flask(__name__, static_folder=None)

# the site lives one level up from backend/ ~never serve our own folder,
# it holds .env and credentials.json
BLOCKED_TOPLEVEL = {"backend", ".git", ".claude", "node_modules"}

_hits = defaultdict(list)


def _rate_limited(ip):
    """Crude in-memory throttle. Fine for one process; use redis if you scale out."""
    window = timedelta(minutes=config.RATE_LIMIT_WINDOW_MIN)
    now = datetime.now()
    recent = [t for t in _hits[ip] if now - t < window]
    _hits[ip] = recent
    if len(recent) >= config.RATE_LIMIT_MAX:
        return True
    recent.append(now)
    return False


@app.after_request
def _cors(response):
    if config.ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = config.ALLOWED_ORIGIN
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.get("/")
def index():
    return send_from_directory(config.PROJECT_ROOT, "index.html")


@app.get("/<path:filename>")
def static_files(filename):
    parts = PurePosixPath(filename).parts
    if not parts or parts[0] in BLOCKED_TOPLEVEL or parts[0].startswith("."):
        abort(404)
    return send_from_directory(config.PROJECT_ROOT, filename)


@app.route("/api/submit", methods=["POST", "OPTIONS"])
def submit():
    if request.method == "OPTIONS":
        return ("", 204)

    ip = request.headers.get("X-Forwarded-For", request.remote_addr or "?").split(",")[0].strip()
    if _rate_limited(ip):
        return jsonify(ok=False, message="Bạn gửi hơi nhanh, thử lại sau ít phút nhé."), 429

    values = validators.clean(request.get_json(silent=True))

    # a bot tripped the honeypot ~answer like nothing happened, store nothing
    if validators.is_bot(values):
        log.info("honeypot hit from %s", ip)
        return jsonify(ok=True, message="Đã ghi nhận."), 200

    errors = validators.validate(values)
    if errors:
        return jsonify(ok=False, errors=errors, message="Bạn kiểm tra lại các ô được đánh dấu giúp mình nhé."), 400

    try:
        if sheets.has_recent_duplicate(values["email"], config.DUPLICATE_WINDOW_HOURS):
            log.info("duplicate within window: %s", values["email"])
            return jsonify(ok=True, message="Chúng tôi đã nhận được thông tin của bạn rồi nhé."), 200

        sheets.append_lead(values)
    except Exception:
        log.exception("could not write to the sheet")
        return jsonify(ok=False, message="Hệ thống đang bận, bạn thử lại sau ít phút nhé."), 500

    log.info("new lead: %s <%s>", values["name"], values["email"])
    return jsonify(ok=True, message="Cảm ơn bạn! Chúng tôi sẽ liên hệ tư vấn sớm nhất."), 201


@app.get("/api/health")
def health():
    """Quick way to prove the credentials and sheet sharing are actually right."""
    try:
        count = len(sheets.fetch_leads())
    except Exception as exc:
        return jsonify(ok=False, sheet="lỗi", detail=str(exc)[:300]), 500
    return jsonify(ok=True, sheet="ok", leads=count), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=config.PORT, debug=config.DEBUG)
