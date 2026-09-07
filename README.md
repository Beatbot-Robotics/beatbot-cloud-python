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
    state_callback=async_handle_state,
    device_added_callback=async_handle_device_added,
    device_removed_callback=async_handle_device_removed,
    reconnect_callback=async_handle_reconnect,
    token_refresh_callback=async_refresh_access_token,
)
await events.async_run()
```

The caller provides an access token or a synchronous/asynchronous token provider.
The library owns REST request construction and WebSocket reconnection; applications
can register callbacks for events, successful reconnections, and rejected-token
refreshes. State callbacks receive a `BeatbotEvent`, which can be applied with
`event.apply_to(device)`. Device-added and device-removed callbacks receive the
device ID. The library routes cloud event types and ignores unknown types for
these specialized callbacks. All callbacks may be synchronous or asynchronous.
The optional positional `event_callback` remains supported and receives all events.

## Development

```bash
python -m pip install -e '.[test]'
pytest
ruff check .
ruff format --check .
python -m build
```
