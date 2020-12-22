from flask import Flask, request
import patreon_importer
import fanbox_importer
import subscribestar_importer
import threading
app = Flask(__name__)

@app.route('/api/import', methods=['POST'])
def import_api():
    if not request.args.get('session_key'):
        return "", 401
    if request.args.get('service') == 'patreon':
        th = threading.Thread(target=patreon_importer.import_posts, args=(request.args.get('session_key'),))
        th.start()
    elif request.args.get('service') == 'fanbox':
        th = threading.Thread(target=fanbox_importer.import_posts, args=(request.args.get('session_key'),))
        th.start()
    elif request.args.get('service') == 'subscribestar':
        th = threading.Thread(target=subscribestar_importer.import_posts, args=(request.args.get('session_key'),))
        th.start()
    return "", 200