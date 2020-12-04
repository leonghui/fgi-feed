from flask import Flask, request, jsonify
from requests import exceptions

from fgi_feed import get_latest_fgi

app = Flask(__name__)


@app.route('/', methods=['GET'])
def form():
    try:
        output = get_latest_fgi()
        response = jsonify(output)
        response.mimetype = 'application/feed+json'
        return response
    except exceptions.RequestException:
        return f"Error generating output for CNN Fear & Greed Index."


if __name__ == '__main__':
    app.run(host='0.0.0.0')
