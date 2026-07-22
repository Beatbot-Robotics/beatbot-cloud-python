# beatbot-cloud

`beatbot-cloud` is the asynchronous Python client for Beatbot cloud accounts.
It provides region-aware REST access, typed device models, and a WebSocket event
transport without depending on Home Assistant.

```python
from beatbot_cloud import BeatbotClient

client = BeatbotClient(region="na", requester=oauth_request)
devices = await client.get_devices()
```

The caller owns authentication. `requester` is an async callable compatible
with `aiohttp.ClientSession.request`; it may add or refresh OAuth credentials
before forwarding the request.

## Development

```bash
python -m pip install -e '.[test]'
pytest
ruff check .
ruff format --check .
python -m build
```

