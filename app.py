from fastapi.applications import FastAPI
import uvicorn

from fgi_feed import ROUNDING, get_latest_fgi
from json_feed_data import JsonFeedTopLevel

app: FastAPI = FastAPI()
# app.config.update({'JSONIFY_MIMETYPE': 'application/feed+json'})


@app.get(path="/")
@app.get(path="/{method}")
def root(method: ROUNDING | None = None):
    result: JsonFeedTopLevel = get_latest_fgi(method)
    return result.model_dump(exclude_unset=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
