from flask import Flask, jsonify, abort
from flask.logging import create_logger

from fgi_feed import get_latest_fgi, ROUND

app = Flask(__name__)
logger = create_logger(app)


@app.route('/', methods=['GET'])
def root():
    output = get_latest_fgi(logger=logger)

    return jsonify(output)


@app.route('/<method>', methods=['GET'])
def rounded(method):
    if method == 'hourly':
        output = get_latest_fgi(logger=logger, method=ROUND.HOUR)
    elif method == 'hourly_open':
        output = get_latest_fgi(logger=logger, method=ROUND.HOUR_OPEN)
    elif method == 'daily':
        output = get_latest_fgi(logger=logger, method=ROUND.DAY)
    else:
        abort(500, description='Error, invalid rounding method')

    return jsonify(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
