import json
import os

import gnupg
from flask import Flask, Response, render_template, send_from_directory

TRS_LOCATION = os.environ.get("TRS_LOCATION", "/home/ubuntu/trs.jsonld")
if not os.path.exists(TRS_LOCATION):
    raise FileNotFoundError(f"TRS file not found at {TRS_LOCATION}")
TRS = json.load(open(TRS_LOCATION, "r"))
GPG_HOME = os.environ.get("GPG_HOME", "/home/ubuntu/.gnupg")
GPG_FINGERPRINT = os.environ.get("GPG_FINGERPRITN", TRS["trov:gpgFingerprint"])
try:
    gpg = gnupg.GPG(gnupghome=GPG_HOME)
    GPG_KEYID = gpg.list_keys().key_map[GPG_FINGERPRINT]["keyid"]
except KeyError:
    raise RuntimeError("Configured GPG_FINGERPRINT not found.")

app = Flask(__name__)


@app.route("/pubkey", methods=["GET"])
def send_pubkey():
    """Export server's gpg key as a file."""
    return Response(gpg.export_keys(GPG_KEYID), mimetype="text/plain")


@app.route("/", methods=["GET"])
def default_html_index():
    """Default index page."""
    data = {
        "trace_server_id": TRS["trov:url"],
        "trace_server_public_key": TRS["trov:gpgFingerprint"],
        "fnames": [_[:-4] for _ in os.listdir("data") if _.endswith(".sig")],
    }
    return render_template("index.html", **data)


@app.route("/run/<path:path>", methods=["GET"])
def send_run(path):
    """Serve static files from storage dir."""
    return send_from_directory("data", path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
