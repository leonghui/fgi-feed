# fgi-feed
A simple Python script to generate a [JSON Feed](https://jsonfeed.org/) for the [CNNMoney Fear & Greed Index](https://edition.cnn.com/markets/fear-and-greed).

Served over [Flask!](https://github.com/pallets/flask/)

Use the [Docker build](https://github.com/users/leonghui/packages/container/package/fgi-feed) to host your own instance.

1. Set your timezone as an environment variable (see [docker docs]): `TZ=America/Los_Angeles` 

2. Access the feed using the URL: `http://<host>:5000/`

By default, the latest Fear & Greed Index is used to create a feed item.

To avoid repetitive updates in your RSS reader, you can try the following "rounding" methods:
1. Daily index at previous close: `http://<host>:5000/daily`

2. Hourly index (rounded down): `http://<host>:5000/hourly`

3. Hourly index (if different from previous close, i.e. when markets are open): `http://<host>:5000/hourly_open`

Tested with:
- [Nextcloud News App](https://github.com/nextcloud/news)

[docker docs]:(https://docs.docker.com/compose/environment-variables/#set-environment-variables-in-containers)
