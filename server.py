from flask import Flask, jsonify
from flask.logging import create_logger

from fgi_feed import get_latest_fgi

app = Flask(__name__)
logger = create_logger(app)


@app.route('/', methods=['GET'])
def process_query():
    output = get_latest_fgi(logger)

    return jsonify(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
