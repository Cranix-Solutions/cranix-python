# cranix-python

Common Python modules for [CRANIX](https://github.com/Cranix-Solutions).

The package provides a native REST client for the CRANIX API (so Python code no
longer has to shell out to `crx_api.sh`, `crx_api_text.sh` or
`crx_api_post_file.sh`), the shared helper functions used by `cranix-base` and
`cranix-ms365`, the user import logic and the Microsoft 365 synchronization
helpers.

## Installation

The package is built as the RPM `python313-cranix`:

```
make install DESTDIR=/ PYTHONSITEARCH=/usr/lib/python3.13/site-packages/
```

For local development:

```
pip install -e .
```

## Requirements

* Python >= 3.11
* `requests`
* `bashconfigparser`

## Native API client

The client reads the API token from
`/opt/cranix-java/conf/cranix-api.properties`
(`de.cranix.api.auth.localhost`) and talks to `http://localhost:9080/api`.
The base URL can be overridden with the `CRANIX_API_URL` environment variable.

```python
from cranix import api

client = api.CrxApi()

# JSON response
users = client.get("users/all")

# Text response
domain = client.get("system/configuration/DOMAIN", text=True)

# Write
response = client.put("objects/config/user/1/ms365id/abc")
if not response.ok:
    raise RuntimeError(response.value)
```

Common operations are wrapped as convenience functions:

```python
from cranix import api

api.set_configuration("CHECK_PASSWORD_QUALITY", "no")
user_id = api.user_id_by_uid("jdoe")
role = api.user_role_by_uid("jdoe")
```

## User import

`cranix.user_import.Importer` implements the logic used by
`/usr/sbin/crx_import_user_list.py`.

```python
from cranix.user_import import Importer, main

# called from the command line wrapper
main()
```

## Microsoft 365

```python
from cranix import ms365

ms365.read_token()
ms_id = ms365.get_user_msid(user_id)
```

## License

See [LICENSE](LICENSE).