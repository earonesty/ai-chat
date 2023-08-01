import contextlib
import os
import time

def uuid():
    return os.urandom(16).hex()


@contextlib.contextmanager
def assert_wait_for(func, secs=5):
    t0 = time.monotonic()
    while True:
        try:
            assert func()
            return
        except Exception as e:
            ex = e
        if time.monotonic() > (t0 + secs):
            raise ex


def summarize_json(data, list_limit=5, key_limit=5):
    "Recursively reduce data to just the first X nested keys and list items"
    if not isinstance(data, (list, dict)):
        return data
    if isinstance(data, list):
        return [summarize_json(item, list_limit, key_limit) for item in data[:list_limit]]
    if isinstance(data, dict):
        all_keys = list(data.keys())
        kept_keys = all_keys[:key_limit]
        truncated_keys = all_keys[key_limit:]
        d = dict([
            (key, summarize_json(data[key], list_limit, key_limit))
            for key in kept_keys
        ])
        if truncated_keys:
            d["_truncated_keys"] = truncated_keys
        return d
