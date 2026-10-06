# -*- coding: utf-8 -*-

# Copyright (c) 2026 Peter Varkoly <pvarkoly@cephalix.eu> All rights reserved.

"""
Microsoft 365 synchronization helpers for CRANIX.

CRANIX side calls are done through :mod:`cranix.api`, Microsoft Graph calls
through :mod:`requests`.
"""

import copy
import json
import os
import re
import secrets
import string
import time

import requests

from bashconfigparser import BashConfigParser

from .. import api
from .vars import GROUPIDS_DIR
from .vars import FAILED_DIR
from .vars import MS365_DIR
from .vars import USERIDS_DIR
from .vars import config_file
from .vars import msgroup
from .vars import msteam
from .vars import msuser
from .vars import token_file

# Global state
now = int(time.time())
fnow = time.strftime("%Y-%m-%d.%H-%M-%S")
token = {}
Header = {}

_parser = BashConfigParser(config_file=config_file)
config = _parser.get_all_variables()
debug = config.get('DEBUG', 'no').lower() != 'no'

_client = api.client()


def _ensure_dirs():
    for directory in (MS365_DIR, USERIDS_DIR, GROUPIDS_DIR, FAILED_DIR):
        os.makedirs(directory, exist_ok=True)


def _write_json(path, obj):
    try:
        _ensure_dirs()
        with open(path, 'w') as handle:
            if isinstance(obj, str):
                handle.write(obj)
            else:
                json.dump(obj, handle, ensure_ascii=False, indent=2)
    except OSError:
        pass


def get_token():
    """Request a new access token from Microsoft and store it."""
    global token
    tenant = config.get('TENANT_ID', '')
    params = {
        "tenant": tenant,
        "client_id": config.get('CLIENT_ID', ''),
        "scope": "https://graph.microsoft.com/.default",
        "client_secret": config.get('SECRET', ''),
        "grant_type": "client_credentials",
    }
    url = "https://login.microsoftonline.com/{0}/oauth2/v2.0/token".format(tenant)
    if debug:
        print("get_token")
    try:
        response = requests.post(
            url, data=params,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=60)
        token = response.json()
    except (requests.RequestException, ValueError) as error:
        raise RuntimeError("Can not get MS365 token: {0}".format(error))
    token['ext_expires_in'] = int(time.time()) + 2400
    with open(token_file, 'w') as handle:
        json.dump(token, handle, ensure_ascii=False)
    if debug:
        print(token)
    return token


def read_token(force=False):
    """Return a valid access token, refreshing it if necessary."""
    global token
    current = int(time.time())
    if not force:
        try:
            with open(token_file, 'r') as handle:
                token = json.load(handle)
            if token.get('ext_expires_in', 0) > current:
                return token['access_token']
        except (FileNotFoundError, ValueError):
            pass
    get_token()
    return token['access_token']


def graph_headers():
    """Return the headers used for Microsoft Graph requests."""
    global Header
    Header = {
        "Authorization": "Bearer " + str(read_token()),
        "Content-Type": "application/json",
    }
    return Header


def _graph_request(method, url, data=None, success=(200, 201, 202, 204),
                   tag="graph"):
    """Perform a Microsoft Graph request and log failures."""
    headers = graph_headers()
    try:
        response = requests.request(method, url, headers=headers, json=data,
                                    timeout=60)
    except requests.RequestException as error:
        _write_json(os.path.join(FAILED_DIR, "{0}-{1}.json".format(tag, fnow)),
                    {"url": url, "data": data, "error": str(error)})
        return None
    if response.status_code in success:
        if debug:
            _write_json(os.path.join(MS365_DIR, "{0}-{1}.json".format(tag, fnow)),
                        response.text or str(response.status_code))
    else:
        _write_json(os.path.join(FAILED_DIR, "{0}-{1}.json".format(tag, fnow)),
                    {"url": url, "data": data, "status": response.status_code,
                     "response": response.text})
    return response


def cranix_user_to_ms(user):
    """Convert a CRANIX user into a Microsoft 365 user object."""
    if debug:
        print('cranix_user_to_ms')
    result = copy.deepcopy(msuser)
    domain = config.get('OFFICE_DOMAIN', '')
    if user['role'] == 'students':
        result['jobTitle'] = 'Schüler'
        if config.get('DOMAIN_STUDENTS', '') != "":
            domain = config['DOMAIN_STUDENTS']
    elif user['role'] == 'teachers':
        result['jobTitle'] = 'Lehrer'
        if config.get('DOMAIN_TEACHERS', '') != "":
            domain = config['DOMAIN_TEACHERS']
    elif user['role'] == 'parent':
        result['jobTitle'] = 'Eltern'
    elif user['role'] == 'administration':
        result['jobTitle'] = 'Verwaltung'
    elif user['role'] == 'sysadmins':
        result['jobTitle'] = 'Systemadministratoren'
    else:
        result['jobTitle'] = 'Mitarbeiter'

    result['userprincipalname'] = "{0}@{1}".format(user['uid'], domain)
    result['displayName'] = "{0} {1}".format(user['givenname'], user['surname'])
    result['mailnickname'] = user['uid']
    result['givenName'] = user['givenname']
    result['surName'] = user['surname']
    result['state'] = config.get('STATE', '')
    result['city'] = config.get('CITY', '')
    result['country'] = config.get('COUNTRY', '')
    result['usageLocation'] = config.get('COUNTRYISO', '')
    result['passwordProfile']['password'] = user['password']
    if 'group' in user:
        result['department'] = user['group']

    if 'mpassword' in user and user['mpassword'] == 'yes':
        result['passwordProfile']['forceChangePasswordNextSignIn'] = True
        result['passwordProfile']['forceChangePasswordNextSignInWithMfa'] = True
    if debug:
        print(result)
    return result


# Sets the microsoft object ids for the cranix objects saving as CrxConfig object.
def set_user_msid(user_id, ms365_id):
    try:
        result = _client.set_object_config("user", user_id, "ms365id", ms365_id)
        if result is not None and getattr(result, "ok", False):
            return True
    except api.CrxApiError:
        pass
    _write_json(os.path.join(USERIDS_DIR, str(user_id)), str(ms365_id))
    return False


def set_user_msid_byuid(uid, ms365_id):
    user_id = _client.user_id_by_uid(uid)
    if not user_id:
        return False
    return set_user_msid(user_id, ms365_id)


def set_group_msid(group_id, ms365_id):
    try:
        result = _client.set_object_config("group", group_id, "ms365id", ms365_id)
        if result is not None and getattr(result, "ok", False):
            return True
    except api.CrxApiError:
        pass
    _write_json(os.path.join(GROUPIDS_DIR, str(group_id)), str(ms365_id))
    return False


def set_msteamid(group_id, team_id):
    try:
        result = _client.set_object_config("group", group_id, "msteamid", team_id)
        if result is not None and getattr(result, "ok", False):
            return True
    except api.CrxApiError:
        pass
    _write_json(os.path.join(GROUPIDS_DIR, "{0}_team".format(group_id)), str(team_id))
    return False


# Gets the microsoft object ids of the cranix objects saved as CrxConfig objects.
# If the corresponding CrxConfig object does not exist gets the value from the
# deprecated file and saves it as CrxConfig object.
def get_user_msid(user_id):
    ms365_id = ""
    try:
        obj = _client.get_object_config("user", user_id, "ms365id")
        if isinstance(obj, dict):
            ms365_id = obj.get("value", "") or ""
        elif obj:
            ms365_id = str(obj)
    except api.CrxApiError:
        ms365_id = ""
    if ms365_id:
        return ms365_id
    try:
        with open(os.path.join(USERIDS_DIR, str(user_id)), 'r') as handle:
            ms365_id = handle.read().strip()
        if ms365_id:
            set_user_msid(user_id, ms365_id)
    except OSError:
        print('Can not read ms365 id')
    return ms365_id


def get_user_msid_byuid(uid):
    user_id = _client.user_id_by_uid(uid)
    if not user_id:
        return ""
    return get_user_msid(user_id)


def get_group_msid(group_id):
    ms365_id = ""
    try:
        obj = _client.get_object_config("group", group_id, "ms365id")
        if isinstance(obj, dict):
            ms365_id = obj.get("value", "") or ""
        elif obj:
            ms365_id = str(obj)
    except api.CrxApiError:
        ms365_id = ""
    if ms365_id:
        return ms365_id
    try:
        with open(os.path.join(GROUPIDS_DIR, str(group_id)), 'r') as handle:
            ms365_id = handle.read().strip()
        if ms365_id:
            set_group_msid(group_id, ms365_id)
    except OSError:
        print('Can not read ms365 id')
    return ms365_id


def get_group_msid_byname(name):
    group_id = _client.group_id_by_name(name)
    if not group_id:
        return ""
    return get_group_msid(group_id)


def get_msteamid(group_id):
    ms365_id = ""
    try:
        obj = _client.get_object_config("group", group_id, "msteamid")
        if isinstance(obj, dict):
            ms365_id = obj.get("value", "") or ""
        elif obj:
            ms365_id = str(obj)
    except api.CrxApiError:
        ms365_id = ""
    if ms365_id:
        return ms365_id
    try:
        with open(os.path.join(GROUPIDS_DIR, "{0}_team".format(group_id)), 'r') as handle:
            ms365_id = handle.read().strip()
        if ms365_id:
            set_msteamid(group_id, ms365_id)
    except OSError:
        print('Can not read ms365 id')
    return ms365_id


# Deletes the microsoft <-> cranix mapping objects.
def delete_user_msid(user_id):
    try:
        _client.delete_object_config("user", user_id, "ms365id")
    except api.CrxApiError:
        pass
    try:
        os.remove(os.path.join(USERIDS_DIR, str(user_id)))
    except OSError:
        pass


def delete_group_msid(group_id):
    try:
        _client.delete_object_config("group", group_id, "ms365id")
    except api.CrxApiError:
        pass
    try:
        os.remove(os.path.join(GROUPIDS_DIR, str(group_id)))
    except OSError:
        pass


def delete_msteamid(group_id):
    try:
        _client.delete_object_config("group", group_id, "msteamid")
    except api.CrxApiError:
        pass
    try:
        os.remove(os.path.join(GROUPIDS_DIR, "{0}_team".format(group_id)))
    except OSError:
        pass


def add_owner_to_team(tid, msid, u):
    data = {
        "@odata.type": "#microsoft.graph.aadUserConversationMember",
        "roles": ["owner"],
        "user@odata.bind": "https://graph.microsoft.com/v1.0/users('{0}')".format(msid),
    }
    url = "https://graph.microsoft.com/beta/teams/{0}/members".format(tid)
    _graph_request("POST", url, data=data, success=(201,),
                   tag="added_owner_to_msteam-{0}".format(u))


def create_msgroup(ms_name, group):
    name = group['name']
    description = group['description']
    group_id = _client.group_id_by_name(name)
    body = copy.deepcopy(msgroup)
    body["displayName"] = ms_name
    body["mailNickname"] = ms_name
    body["description"] = description
    url = "https://graph.microsoft.com/beta/groups/"
    response = _graph_request("POST", url, data=body, success=(201,),
                              tag="create_msgroup-{0}".format(name))
    if response is not None and response.status_code == 201:
        try:
            set_group_msid(group_id, response.json()['id'])
        except (KeyError, ValueError):
            pass


def create_msteam(ms_name, group):
    name = group['name']
    description = group['description']
    group_id = _client.group_id_by_name(name)
    body = copy.deepcopy(msteam)
    body["displayName"] = ms_name
    body["description"] = description
    url = "https://graph.microsoft.com/beta/teams/"
    response = _graph_request("POST", url, data=body, success=(201, 202),
                              tag="create_msteam-{0}".format(name))
    if response is not None and response.status_code in (201, 202):
        location = response.headers.get('Content-Location', '')
        match = re.search(r"'([^']+)'", location)
        if match:
            set_msteamid(group_id, match.group(1))


def add_user_to_group(group_ms365_id, user_ms365_id, cranix_id):
    data = {
        "@odata.id": "https://graph.microsoft.com/beta/directoryObjects/{0}".format(
            user_ms365_id)
    }
    url = "https://graph.microsoft.com/beta/groups/{0}/members/$ref".format(
        group_ms365_id)
    _graph_request("POST", url, data=data, success=(200, 201, 204),
                   tag="add_to_group-{0}".format(cranix_id))


def remove_user_from_group(group_ms365_id, user_ms365_id, cranix_id):
    url = "https://graph.microsoft.com/beta/groups/{0}/members/{1}/$ref".format(
        group_ms365_id, user_ms365_id)
    _graph_request("DELETE", url, success=(204,),
                   tag="remove_user_from_group-{0}".format(cranix_id))


def add_user_to_team(team_ms365_id, user_ms365_id, cranix_id):
    data = {
        "@odata.type": "#microsoft.graph.aadUserConversationMember",
        "roles": ["member"],
        "user@odata.bind": "https://graph.microsoft.com/v1.0/users('{0}')".format(
            user_ms365_id),
    }
    url = "https://graph.microsoft.com/beta/teams/{0}/members".format(team_ms365_id)
    _graph_request("POST", url, data=data, success=(201,),
                   tag="add_to_team-{0}".format(cranix_id))


def remove_user_from_team(team_ms365_id, user_ms365_id, cranix_id):
    url = "https://graph.microsoft.com/beta/teams/{0}/members/{1}".format(
        team_ms365_id, user_ms365_id)
    _graph_request("DELETE", url, success=(204,),
                   tag="remove_user_from_team-{0}".format(cranix_id))


def cranix_user_id(uid):
    """Return the CRANIX user id for an uid."""
    return _client.user_id_by_uid(uid)


def cranix_user_role(uid):
    """Return the role of a CRANIX user identified by its uid."""
    return _client.user_role_by_uid(uid)


def cranix_user_role_by_id(user_id):
    """Return the role of a CRANIX user identified by its id."""
    user = _client.get("users/{0}".format(user_id))
    if isinstance(user, dict):
        return user.get('role', '')
    return ""


def create_ms_user(ms_user):
    """Create a Microsoft 365 user and return its object id."""
    response = _graph_request("POST", "https://graph.microsoft.com/beta/users",
                              data=ms_user, success=(201,), tag="add_user")
    if response is not None and response.status_code == 201:
        try:
            return response.json().get('id')
        except ValueError:
            return None
    return None


def update_ms_user(ms_id, ms_user):
    """Update an existing Microsoft 365 user."""
    response = _graph_request(
        "PATCH", "https://graph.microsoft.com/beta/users/{0}".format(ms_id),
        data=ms_user, success=(200, 204), tag="modify_user")
    return response is not None and response.status_code in (200, 204)


def delete_ms_user(ms_id):
    """Delete a Microsoft 365 user."""
    response = _graph_request(
        "DELETE", "https://graph.microsoft.com/beta/users/{0}".format(ms_id),
        success=(204,), tag="delete_user")
    return response is not None and response.status_code == 204


def assign_license(ms_id, add_licenses, remove_licenses=None):
    """Assign licenses to a Microsoft 365 user."""
    data = {
        "addLicenses": add_licenses,
        "removeLicenses": remove_licenses or [],
    }
    response = _graph_request(
        "POST",
        "https://graph.microsoft.com/beta/users/{0}/assignLicense".format(ms_id),
        data=data, success=(200,), tag="assign_license")
    return response is not None and response.status_code == 200


def get_all_users():
    """Yield all Microsoft 365 users, following pagination."""
    url = "https://graph.microsoft.com/beta/users"
    while url:
        response = _graph_request("GET", url, success=(200,), tag="list_users")
        if response is None:
            return
        try:
            data = response.json()
        except ValueError:
            return
        for user in data.get('value', []):
            yield user
        url = data.get('@odata.nextLink')


def generate_office365_password(length=16, require_upper=True, require_lower=True,
                                require_digit=True, require_symbol=True,
                                allow_repeats=False):
    if length < (require_upper + require_lower + require_digit + require_symbol):
        raise ValueError("Length too short für die geforderten Komplexitätsanforderungen.")

    upper = string.ascii_uppercase
    lower = string.ascii_lowercase
    digits = string.digits
    symbols = '#$!?'

    pool = ""
    required = []

    if require_upper:
        required.append(secrets.choice(upper))
        pool += upper
    if require_lower:
        required.append(secrets.choice(lower))
        pool += lower
    if require_digit:
        required.append(secrets.choice(digits))
        pool += digits
    if require_symbol:
        required.append(secrets.choice(symbols))
        pool += symbols

    remaining = length - len(required)
    if remaining > 0:
        pool_chars = pool if pool else (upper + lower + digits + symbols)
        for _ in range(remaining):
            required.append(secrets.choice(pool_chars))

    if not allow_repeats:
        for i in range(1, len(required)):
            if required[i] == required[i - 1]:
                alt = secrets.choice(pool_chars)
                while alt == required[i - 1]:
                    alt = secrets.choice(pool_chars)
                required[i] = alt

    secrets.SystemRandom().shuffle(required)

    return "".join(required)


if __name__ == "__main__":
    print(generate_office365_password(
        length=16, require_upper=True, require_lower=True,
        require_digit=True, require_symbol=True, allow_repeats=False))