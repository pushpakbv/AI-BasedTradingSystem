import os
import json
import threading
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sock import Sock
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

app = Flask(__name__)
CORS(app)
sock = Sock(app)

FINAL_PREDICTIONS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../data_processor_service/final_predictions'))
ws_clients = set()

@app.route('/api/prediction/<ticker>')
def get_prediction(ticker):
    ticker = ticker.upper()
    file_path = os.path.join(FINAL_PREDICTIONS_DIR, f"{ticker}_prediction.json")
    if os.path.exists(file_path):
        with open(file_path) as f:
            return jsonify(json.load(f))
    return jsonify({"error": "Prediction not found"}), 404

@sock.route('/ws')
def ws(sock):
    ws_clients.add(sock)
    try:
        while True:
            data = sock.receive()
            if data is None:
                break
    finally:
        ws_clients.remove(sock)

def broadcast_prediction_update(ticker):
    file_path = os.path.join(FINAL_PREDICTIONS_DIR, f"{ticker}_prediction.json")
    if os.path.exists(file_path):
        with open(file_path) as f:
            data = json.load(f)
        for client in list(ws_clients):
            try:
                client.send(json.dumps({
                    "type": "prediction_update",
                    "ticker": ticker,
                    "data": data
                }))
            except Exception:
                ws_clients.discard(client)

class PredictionFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if event.is_directory or not event.src_path.endswith('_prediction.json'):
            return
        ticker = os.path.basename(event.src_path).split('_')[0]
        broadcast_prediction_update(ticker)

def start_file_watcher():
    event_handler = PredictionFileHandler()
    observer = Observer()
    observer.schedule(event_handler, FINAL_PREDICTIONS_DIR, recursive=False)
    observer.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    threading.Thread(target=start_file_watcher, daemon=True).start()
    app.run(host='0.0.0.0', port=3000)