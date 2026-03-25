from fastapi.applications import FastAPI
from fgi_feed import ROUNDING, get_latest_fgi
from json_feed_data import JsonFeedTopLevel
import uvicorn
from uvicorn.config import LOGGING_CONFIG

app: FastAPI = FastAPI()

log_config = LOGGING_CONFIG
log_config["formatters"]["access"]["fmt"] = (
    '%(asctime)s - %(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s'
)
log_config["formatters"]["default"]["fmt"] = "%(asctime)s - %(levelprefix)s %(message)s"


@app.get(path="/")
@app.get(path="/{method}")
def root(method: ROUNDING | None = None):
    result: JsonFeedTopLevel = get_latest_fgi(method)
    return result.model_dump(exclude_unset=True)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=log_config)
