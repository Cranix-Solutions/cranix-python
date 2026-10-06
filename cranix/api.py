# -*- coding: utf-8 -*-

# Copyright (c) 2026 Peter Varkoly <pvarkoly@cephalix.eu> All rights reserved.

"""
Native REST client for the CRANIX API.

This module replaces the shell helpers ``crx_api.sh``, ``crx_api_text.sh`` and
``crx_api_post_file.sh`` for Python code. It talks directly to the CRANIX API
on ``http://localhost:9080/api`` using :mod:`requests`.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import requests

from . import config


class CrxApiError(Exception):
    """Raised when the CRANIX API can not be reached or returns an error."""

    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


@dataclass
class CrxResponse:
    """Mirror of the Java ``CrxResponse`` object returned by the API."""

    code: str = ""
    value: str = ""
    parameters: List[str] = field(default_factory=list)
    object_id: Optional[int] = None

    @property
    def ok(self) -> bool:
        return self.code == "OK"

    @classmethod
    def from_json(cls, data: Dict[str, Any]) -> "CrxResponse":
        return cls(
            code=data.get("code", ""),
            value=data.get("value", ""),
            parameters=data.get("parameters") or [],
            object_id=data.get("objectId"),
        )

    def raise_for_status(self) -> "CrxResponse":
        if not self.ok:
            raise CrxApiError(self.value or self.code)
        return self


def _to_response(data: Any) -> Any:
    """Wrap a JSON dict containing ``code`` into a :class:`CrxResponse`."""
    if isinstance(data, dict) and "code" in data:
        return CrxResponse.from_json(data)
    return data


class CrxApi:
    """Thin client around the CRANIX REST API."""

    def __init__(self, base_url=None, token=None, properties_file=None,
                 session=None, timeout=60):
        self.base_url = (base_url or config.get_base_url()).rstrip("/")
        self._properties_file = properties_file
        self._token = token
        self.timeout = timeout
        self.session = session or requests.Session()

    @property
    def token(self) -> str:
        if self._token is None:
            self._token = config.read_token(self._properties_file)
        return self._token

    def _url(self, path: str) -> str:
        return "{0}/{1}".format(self.base_url, path.lstrip("/"))

    def _headers(self, text: bool, has_body: bool) -> Dict[str, str]:
        headers = {"Accept": "text/plain" if text else "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        if has_body:
            headers["Content-Type"] = "application/json"
        return headers

    def request(self, method, path, data=None, text=False, timeout=None,
                **kwargs):
        """Perform a request and return the parsed result.

        JSON responses are returned as Python objects. When ``text`` is true
        the raw response body is returned as string.
        """
        is_json = isinstance(data, (dict, list))
        headers = self._headers(text, is_json)
        if is_json:
            kwargs["json"] = data
        elif data is not None:
            kwargs["data"] = data
        try:
            response = self.session.request(
                method, self._url(path), headers=headers,
                timeout=timeout or self.timeout, **kwargs)
        except requests.RequestException as error:
            raise CrxApiError(str(error)) from error
        if response.status_code >= 400:
            raise CrxApiError(
                "HTTP {0} for {1} {2}: {3}".format(
                    response.status_code, method, path, response.text),
                status_code=response.status_code, response=response)
        if text:
            return response.text
        if not response.content:
            return None
        try:
            return response.json()
        except ValueError:
            return response.text

    def get(self, path, text=False, **kwargs):
        return self.request("GET", path, text=text, **kwargs)

    def post(self, path, data=None, text=False, **kwargs):
        return _to_response(
            self.request("POST", path, data=data, text=text, **kwargs))

    def put(self, path, data=None, text=False, **kwargs):
        return _to_response(
            self.request("PUT", path, data=data, text=text, **kwargs))

    def patch(self, path, data=None, text=False, **kwargs):
        return _to_response(
            self.request("PATCH", path, data=data, text=text, **kwargs))

    def delete(self, path, data=None, text=False, **kwargs):
        return _to_response(
            self.request("DELETE", path, data=data, text=text, **kwargs))

    def upload(self, path, file_path, field="file", form=None, text=False):
        """Upload a file as ``multipart/form-data``."""
        headers = {"Accept": "text/plain" if text else "application/json"}
        if self.token:
            headers["Authorization"] = "Bearer " + self.token
        with open(file_path, "rb") as handle:
            files = {field: handle}
            try:
                response = self.session.request(
                    "POST", self._url(path), headers=headers,
                    data=form or {}, files=files, timeout=self.timeout)
            except requests.RequestException as error:
                raise CrxApiError(str(error)) from error
        if response.status_code >= 400:
            raise CrxApiError(
                "HTTP {0} for POST {1}: {2}".format(
                    response.status_code, path, response.text),
                status_code=response.status_code, response=response)
        if text:
            return response.text
        try:
            return _to_response(response.json())
        except ValueError:
            return response.text

    # -- convenience helpers ------------------------------------------------

    def get_configuration(self, key):
        value = self.get("system/configuration/" + key, text=True)
        return value.rstrip("\n") if value else ""

    def set_configuration(self, key, value):
        return self.put("system/configuration/{0}/{1}".format(key, value))

    def users_by_role(self, role):
        return self.get("users/byRole/" + role) or []

    def user_id_by_uid(self, uid):
        value = self.get("users/byUid/{0}/id".format(uid), text=True)
        return value.strip() if value else ""

    def user_role_by_uid(self, uid):
        value = self.get("users/byUid/{0}/role".format(uid), text=True)
        return value.strip() if value else ""

    def user_by_uid(self, uid):
        user_id = self.user_id_by_uid(uid)
        if not user_id:
            return None
        return self.get("users/" + user_id)

    def group_id_by_name(self, name):
        value = self.get("groups/byName/{0}/id".format(name), text=True)
        return value.strip() if value else ""

    def group_by_name(self, name):
        group_id = self.group_id_by_name(name)
        if not group_id:
            return None
        return self.get("groups/" + group_id)

    def groups_by_type(self, group_type):
        return self.get("groups/byType/" + group_type) or []

    def group_names_by_type(self, group_type):
        value = self.get("groups/text/byType/" + group_type, text=True)
        return [line.strip() for line in (value or "").splitlines() if line.strip()]

    def add_user(self, user):
        return self.post("users/insert", user)

    def modify_user(self, user):
        return self.post("users/{0}".format(user["id"]), user)

    def delete_user(self, uid):
        return self.delete("users/text/{0}".format(uid), text=True)

    def add_group(self, group):
        return self.post("groups/add", group)

    def delete_group(self, name):
        return self.delete("groups/text/{0}".format(name), text=True)

    def add_member(self, group, user):
        return self.put("users/text/{0}/groups/{1}".format(user, group), text=True)

    def remove_member(self, group, user):
        return self.delete(
            "users/text/{0}/groups/{1}".format(user, group), text=True)

    def get_object_config(self, object_type, object_id, key):
        return self.get("objects/config/{0}/{1}/{2}".format(
            object_type, object_id, key))

    def set_object_config(self, object_type, object_id, key, value):
        return self.put("objects/config/{0}/{1}/{2}/{3}".format(
            object_type, object_id, key, value))

    def delete_object_config(self, object_type, object_id, key):
        return self.delete("objects/config/{0}/{1}/{2}".format(
            object_type, object_id, key))


_default_client = None


def client() -> CrxApi:
    """Return a lazily created default :class:`CrxApi` instance."""
    global _default_client
    if _default_client is None:
        _default_client = CrxApi()
    return _default_client


def get_configuration(key):
    return client().get_configuration(key)


def set_configuration(key, value):
    return client().set_configuration(key, value)


def user_id_by_uid(uid):
    return client().user_id_by_uid(uid)


def user_role_by_uid(uid):
    return client().user_role_by_uid(uid)


def user_by_uid(uid):
    return client().user_by_uid(uid)


def users_by_role(role):
    return client().users_by_role(role)


def group_id_by_name(name):
    return client().group_id_by_name(name)


def group_by_name(name):
    return client().group_by_name(name)


def groups_by_type(group_type):
    return client().groups_by_type(group_type)


def group_names_by_type(group_type):
    return client().group_names_by_type(group_type)