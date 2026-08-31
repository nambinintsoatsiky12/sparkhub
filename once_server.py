from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="once", static_url_path="")


@app.route("/")
def home():
    return send_from_directory("once", "index.html")


@app.after_request
def headers(resp):
    resp.headers["Permissions-Policy"] = "camera=*, microphone=*, autoplay=*"
    resp.headers["Content-Security-Policy"] = "frame-ancestors *"
    resp.headers.pop("X-Frame-Options", None)
    return resp


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
