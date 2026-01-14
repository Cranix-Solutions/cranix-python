import json
import os
import sys
import csv

from ._vars import attr_ext_name

from ._functions import read_birthday

def read_classes() -> list[str]:

    classes = []
    for group in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/class').readlines():
        classes.append(group.strip().upper())

    return classes

def read_groups():

    groups = []
    for group in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/workgroups').readlines():
        groups.append(group.strip().upper())

    return groups

all_groups.extend(read_groups())


def read_users(role: str, identifier: str = "sn-gn-bd", debug: bool = False) -> Dict[str, Dict[str, Any]]:

    all_users = {}

    cmd = f'/usr/sbin/crx_api.sh GET users/byRole/{role}'
    users_data = json.load(os.popen(cmd))

    for user in users_data:

        if identifier == "sn-gn-bd":
            user_id = f"{user['surName'].upper()}-{user['givenName'].upper()}-{user['birthDay']}"
        else:
            user_id = str(user.get(identifier, "unknown"))

        user_id = user_id.replace(' ', '_')
        all_users[user_id] = dict(user)

    if debug:
        print("All existing users:")
        print(all_users)

    return all_users

def build_user_id(user: dict, identifier: str) -> str:

    if identifier == "sn-gn-bd":
        uid = f"{user['surName']}-{user['givenName']}-{user['birthDay']}"

    else:
        uid = user.get(identifier, "")

    return uid.upper().replace(" ", "_")

def read_csv(path: str, identifier: str = "sn-gn-bd", debug: bool = False) -> dict:

    users = {}

    with open(path, newline='', encoding='utf-8') as csvfile:

        dialect = csv.Sniffer().sniff(csvfile.readline())
        csvfile.seek(0)

        reader = csv.DictReader(csvfile, dialect=dialect)

        for line_no, row in enumerate(reader, start=1):
            user = {}

            for key, value in row.items():
                if not key:
                    continue

                try:
                    user[attr_ext_name[key.upper()]] = value

                except KeyError:
                    continue

            if 'birthDay' in user:
                try:
                    user['birthDay'] = read_birthday(user['birthDay'])

                except ValueError:
                    user['birthDay'] = ""

            if 'uid' in user:
                user['uid'] = user['uid'].lower()

            user_id = build_user_id(user, identifier)
            users[user_id] = user

    return users


def check_attributes(user, line_count):

    if 'surName' not in user or 'givenName' not in user:
        log_error('Missing required attributes in line {0}.'.format(line_count))
        if debug:
            print('Missing required attributes in line {0}.'.format(line_count))
        return False
    if user['surName'] == "" or user['givenName'] == "":
        log_error('Required attributes are empty in line {0}.'.format(line_count))
        if debug:
            print('Required attributes are empty in line {0}.'.format(line_count))
        return False
    if identifier == "sn-gn-bd":
        if 'birthDay' not in user or user['birthDay'] == '':
            log_error('Missing birthday in line {0}.'.format(line_count))
            if debug:
                print('Missing birthday in line {0}.'.format(line_count))
            return False
    elif not identifier in user:
        log_error('The line {0} does not contains the identifier {1}'.format(line_count,identifier))
        if debug:
            print('The line {0} does not contains the identifier {1}'.format(line_count,identifier))
        return False
    return True

def log_debug(text, obj, debug=True):
    if debug:
        print(text)
        print(obj)

def close(check_password: bool):
    if check_pw:
        os.system("/usr/sbin/crx_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/yes")
    else:
        os.system("/usr/sbin/crx_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/no")
    os.remove(lockfile)
    log_msg("Import finished","OK")

def close_on_error(msg, check_password: bool):
    if check_pw:
        os.system("/usr/sbin/crx_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/yes")
    else:
        os.system("/usr/sbin/crx_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/no")
    os.remove(lockfile)
    log_error(msg)
    log_msg("Import finished","ERROR")
    sys.exit(1)