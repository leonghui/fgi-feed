from flask import Flask, jsonify, abort
from flask.logging import create_logger
from fgi_feed import get_latest_fgi

app = Flask(__name__)
logger = create_logger(app)

@app.route('/', methods=['GET'])
def form():
    try:
        output = get_latest_fgi(logger)
        response = jsonify(output)
        response.mimetype = 'application/feed+json'
        return response
    except Exception:
        abort(500, description='Error generating output')


if __name__ == '__main__':
    app.run(host='0.0.0.0')
