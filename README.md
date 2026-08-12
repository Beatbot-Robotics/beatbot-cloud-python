# beatbot-cloud

`beatbot-cloud` is the asynchronous Python client for Beatbot cloud accounts.
It provides region-aware REST access, typed device models, and a WebSocket event
transport without depending on Home Assistant.

```python
from beatbot_cloud import BeatbotClient, BeatbotEventClient

client = BeatbotClient(
    region="na",
    session=session,
    access_token=async_get_access_token,
)
devices = await client.get_devices()

events = BeatbotEventClient(
    session,
    client.event_stream_url,
    client.async_get_access_token,
    async_handle_event,
    reconnect_callback=async_handle_reconnect,
    token_refresh_callback=async_refresh_access_token,
)
await events.async_run()
```

The caller provides an access token or a synchronous/asynchronous token provider.
The library owns REST request construction and WebSocket reconnection; applications
can register callbacks for events, successful reconnections, and rejected-token
refreshes.

## Development

```bash
python -m pip install -e '.[test]'
pytest
ruff check .
ruff format --check .
python -m build
```
