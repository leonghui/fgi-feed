# fgi-feed
A simple Python script to generate a [JSON Feed](https://jsonfeed.org/) for the [CNNMoney Fear & Greed Index](https://money.cnn.com/data/fear-and-greed/).

Uses [BeautifulSoup 4](https://www.crummy.com/software/BeautifulSoup/) and served over [Flask!](https://github.com/pallets/flask/)

Use the [Docker build](https://github.com/users/leonghui/packages/container/package/fgi-feed) to host your own instance.

1. Set your timezone as an environment variable (see [docker docs]): `TZ=America/Los_Angeles` 

2. Access the feed using the URL: `http://<host>:5000/`

Tested with:
- [Nextcloud News App](https://github.com/nextcloud/news)

[docker docs]:(https://docs.docker.com/compose/environment-variables/#set-environment-variables-in-containers)
