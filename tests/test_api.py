# -*- coding: utf-8 -*-

import json

import pytest

from cranix import api


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=None):
        self.status_code = status_code
        self._payload = payload
        if text is not None:
            self._text = text
        elif payload is not None:
            self._text = json.dumps(payload)
        else:
            self._text = ""
        self.content = self._text.encode()

    @property
    def text(self):
        return self._text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        return self.response


def make_client(response, token="tok"):
    session = FakeSession(response)
    client = api.CrxApi(base_url="http://api.test/api", token=token, session=session)
    return client, session


def test_get_json_sets_auth_header():
    client, session = make_client(FakeResponse(payload=[{"uid": "a"}]))
    assert client.get("users/all") == [{"uid": "a"}]
    method, url, kwargs = session.calls[0]
    assert method == "GET"
    assert url == "http://api.test/api/users/all"
    assert kwargs["headers"]["Authorization"] == "Bearer tok"
    assert kwargs["headers"]["Accept"] == "application/json"


def test_get_text():
    client, session = make_client(FakeResponse(text="example.com"))
    assert client.get("system/configuration/DOMAIN", text=True) == "example.com"
    assert session.calls[0][2]["headers"]["Accept"] == "text/plain"


def test_put_wraps_crx_response():
    response = FakeResponse(payload={
        "code": "OK", "value": "done",
        "parameters": ["u"], "objectId": 7,
    })
    client, _ = make_client(response)
    result = client.put("objects/config/user/7/ms365id/abc")
    assert isinstance(result, api.CrxResponse)
    assert result.ok
    assert result.object_id == 7
    assert result.parameters == ["u"]


def test_http_error_raises():
    client, _ = make_client(FakeResponse(status_code=500, text="boom"))
    with pytest.raises(api.CrxApiError):
        client.get("users/all")


def test_error_code_does_not_raise_but_is_not_ok():
    response = FakeResponse(payload={"code": "ERROR", "value": "nope"})
    client, _ = make_client(response)
    result = client.post("users/insert", {"uid": "x"})
    assert not result.ok
    with pytest.raises(api.CrxApiError):
        result.raise_for_status()


def test_get_configuration_strips_newline():
    client, _ = make_client(FakeResponse(text="example.com\n"))
    assert client.get_configuration("DOMAIN") == "example.com"


def test_group_names_by_type():
    client, _ = make_client(FakeResponse(text="CLASS1\nCLASS2\n\n"))
    assert client.group_names_by_type("class") == ["CLASS1", "CLASS2"]