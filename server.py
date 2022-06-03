from flask import Flask, jsonify
from flask.logging import create_logger

from fgi_feed import get_latest_fgi, ROUND
from mozilla_devices import get_useragent_list, DeviceType


app = Flask(__name__)
app.config.update({'JSONIFY_MIMETYPE': 'application/feed+json'})
logger = create_logger(app)
useragent_list = get_useragent_list(DeviceType.PHONES, logger)


@app.route('/', methods=['GET'])
@app.route('/<method>', methods=['GET'])
def rounded(method=None):
    if method == 'hourly':
        output = get_latest_fgi(logger, useragent_list, method=ROUND.HOUR)
    elif method == 'hourly_open':
        output = get_latest_fgi(logger, useragent_list, method=ROUND.HOUR_OPEN)
    elif method == 'daily':
        output = get_latest_fgi(logger, useragent_list, method=ROUND.DAY)
    else:
        output = get_latest_fgi(logger, useragent_list)

    return jsonify(output)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
