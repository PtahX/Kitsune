from flask import Flask, request
import patreon_importer
import threading
app = Flask(__name__)

@app.route('/api/import')
def import_api():
    if not request.args.get('session_key'):
        return "", 401
    if request.args.get('service') == 'patreon':
        th = threading.Thread(target=patreon_importer.import_posts, args=(request.args.get('session_key'),))
        th.start()
    return "", 200