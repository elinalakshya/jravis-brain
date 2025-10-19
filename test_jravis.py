print("JRAVIS test start")

from flask import Flask
from tinydb import TinyDB

app = Flask(__name__)
db = TinyDB("jr_memory.json")


@app.route("/")
def ok():
    return "JRAVIS OK ✅"


if __name__ == "__main__":
    app.run(port=3300)
