from flask import Flask
from threading import Thread
import os

app = Flask(__name__)

@app.route("/")
def index():
    return "Bot is running!"

def run():
    port = int(os.environ.get("PORT", 10000))  # Render auto port
    app.run(host="0.0.0.0", port=port)

def b():
    server = Thread(target=run)
    server.daemon = True  # ensures thread closes on shutdown
    server.start()
