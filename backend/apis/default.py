from apis.base import app, check_configs, admin
from bottle import static_file

BIN_DIR = "/zeroci/bin/"
STATIC_DIR = "../dist/static"
INDEX_DIR = "../dist"


@app.route("/static/<filepath:path>")
def static(filepath):
    return static_file(filepath, root=STATIC_DIR)


@app.route("/bin/<filepath:path>")
def send_bin(filepath):
    return static_file(filepath, root=BIN_DIR, download=filepath)


@app.route("/initial_config")
@admin
def config():
    return static_file("index.html", root=INDEX_DIR)


@app.route("/")
@app.route("/<path:path>")
@check_configs
def catch_all(path=""):
    return static_file("index.html", root=INDEX_DIR)
