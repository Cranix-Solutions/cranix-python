# -*- coding: utf-8 -*-

# Copyright (c) 2023 Peter Varkoly <pvarkoly@cephalix.eu> Nuremberg, Germany.  All rights reserved.

"""
User import logic for CRANIX.

This module implements the logic behind ``/usr/sbin/crx_import_user_list.py``.
All CRANIX API access is done through :class:`cranix.api.CrxApi` instead of the
shell based ``crx_api*`` helpers.
"""

import csv
import json
import os
import sys
import time

from argparse import ArgumentParser
from typing import Set

from . import api
from . import config
from .functions import check_password
from .functions import check_uid
from .functions import create_secure_pw
from .functions import print_error
from .functions import print_msg
from .functions import read_birthday
from .vars import attr_ext_name
from .vars import user_attributes

DEFAULT_ROLES = ["students", "teachers", "administration", "sysadmins"]
LOCKFILE = '/run/crx_import_user'


def get_roles(client=None):
    """Return the primary group types which can be used as user roles."""
    client = client or api.client()
    try:
        roles = client.group_names_by_type("primary")
    except api.CrxApiError:
        roles = []
    return roles or list(DEFAULT_ROLES)


class Importer:
    """Perform a user import.

    The importer is configured with an argparse namespace (the same options as
    the ``crx_import_user_list.py`` script). Call :meth:`init` to prepare the
    import, then :meth:`run` to execute it.
    """

    def __init__(self, args, client=None):
        self.args = args
        self.client = client or api.CrxApi()
        self.init_debug = False

        # Global state
        self.logs = []
        self.required_classes = []
        self.existing_classes = []
        self.protected_users = []
        self.all_groups = []
        self.all_users = {}
        self.import_list = {}
        self.new_users: Set[str] = set()
        self.new_groups: Set[str] = set()
        self.del_users: Set[str] = set()
        self.del_groups: Set[str] = set()
        self.moved_users: Set[str] = set()
        self.stand_users: Set[str] = set()
        self.date = time.strftime("%Y-%m-%d.%H-%M-%S")
        self.lockfile = LOCKFILE

        # Values resolved during init
        self.check_pw = None
        self.class_adhoc = False
        self.import_dir = ""
        self.password = ""
        self.role = ""
        self.identifier = ""
        self.debug = False
        self.test = False
        self.mustChange = False
        self.resetPassword = False
        self.allClasses = False
        self.cleanClassDirs = False
        self.appendBirthdayToPassword = False
        self.appendClassToPassword = False
        self.fsQuota = 0
        self.fsTeacherQuota = 0
        self.msQuota = 0
        self.msTeacherQuota = 0

        # Read the protected users from the API properties file.
        properties = config.read_properties()
        protected = properties.get('de.cranix.dao.User.protected', '')
        self.protected_users = [p for p in protected.split(",") if p]

    # -- preparation --------------------------------------------------------

    def init(self):
        properties = config.read_properties()
        home_base = self.client.get_configuration("HOME_BASE")
        self.check_pw = self.client.get_configuration(
            "CHECK_PASSWORD_QUALITY").lower() == 'yes'
        self.class_adhoc = self.client.get_configuration(
            "MAINTAIN_ADHOC_ROOM_FOR_CLASSES").lower() == 'yes'
        self.fsQuota = int(self.client.get_configuration("FILE_QUOTA") or 0)
        self.fsTeacherQuota = int(
            self.client.get_configuration("FILE_TEACHER_QUOTA") or 0)
        self.msQuota = int(self.client.get_configuration("MAIL_QUOTA") or 0)
        self.msTeacherQuota = int(
            self.client.get_configuration("MAIL_TEACHER_QUOTA") or 0)

        # Check if an import is already running.
        if os.path.isfile(self.lockfile):
            self.close_on_error("Import is already running")

        self.client.set_configuration("CHECK_PASSWORD_QUALITY", "no")

        args = self.args
        self.password = args.password
        self.role = args.role
        self.identifier = args.identifier
        self.debug = args.debug
        self.test = args.test
        self.mustChange = args.mustChange
        self.resetPassword = args.resetPassword
        self.allClasses = args.allClasses
        self.cleanClassDirs = args.cleanClassDirs
        self.appendBirthdayToPassword = args.appendBirthdayToPassword
        self.appendClassToPassword = args.appendClassToPassword

        self.import_dir = home_base + "/groups/SYSADMINS/userimports/" + self.date
        os.system('mkdir -pm 770 ' + self.import_dir + '/tmp')

        # Create the lock file.
        with open(self.lockfile, 'w') as lock:
            lock.write(self.date)

        # Write the parameters.
        args_dict = dict(args.__dict__)
        args_dict["startTime"] = self.date
        with open(self.import_dir + '/parameters.json', 'w') as handle:
            json.dump(args_dict, handle, ensure_ascii=False)

        self.read_classes()
        self.read_groups()
        self.read_users()
        self.read_csv()

    def read_classes(self):
        self.existing_classes = []
        for group in self.client.group_names_by_type("class"):
            self.existing_classes.append(group.strip().upper())

    def read_groups(self):
        self.all_groups = []
        for group in self.client.group_names_by_type("workgroups"):
            self.all_groups.append(group.strip().upper())

    def read_users(self):
        self.all_users = {}
        for user in self.client.users_by_role(self.role):
            if self.identifier == "sn-gn-bd":
                user_id = (user['surName'].upper() + '-' +
                           user['givenName'].upper() + '-' + user['birthDay'])
            else:
                user_id = user[self.identifier]
            user_id = user_id.replace(' ', '_')
            self.all_users[user_id] = dict(user)
        if self.debug:
            print("All existing user:")
            print(self.all_users)

    def read_csv(self):
        self.import_list = {}
        input_file = self.args.input
        # Copy the import file into the import directory.
        if input_file != self.import_dir + '/userlist.txt':
            os.system('cp {0} {1}/userlist.txt'.format(input_file, self.import_dir))
        # Fix some dos stuff.
        os.system("/usr/bin/dos2unix " + input_file)
        with open(input_file) as csvfile:
            # Detect the type of the csv file.
            try:
                dialect = csv.Sniffer().sniff(csvfile.readline())
            except UnicodeDecodeError:
                self.close_on_error('CVS file is not UTF-8')
            csvfile.seek(0)
            # Create an array of dicts from it.
            csv.register_dialect('cranix', dialect)
            reader = csv.DictReader(csvfile, dialect='cranix')
            if self.init_debug:
                print(reader.fieldnames)
            line_count = 0
            for row in reader:
                line_count = line_count + 1
                user = {}
                user_id = ''
                for key in row:
                    if key == '':
                        continue
                    try:
                        if self.init_debug:
                            print(attr_ext_name[key.upper()] + " " + row[key])
                        user[attr_ext_name[key.upper()]] = row[key]
                    except KeyError:
                        self.log_error('Unknown field "{0}".'.format(key))
                        continue
                    except Exception:
                        self.log_error(
                            'Unknown error accured in line {0}.'.format(line_count))
                        print('Unknown error accured in line {0}.'.format(line_count))
                        print(row)
                        continue
                try:
                    user['birthDay'] = read_birthday(user['birthDay'])
                except SyntaxError:
                    user['birthDay'] = ''
                if not self.check_attributes(user, line_count):
                    if self.debug:
                        print(row)
                    continue
                # uid must be in lower case.
                if 'uid' in user and user['uid']:
                    user['uid'] = user['uid'].lower()
                if self.identifier == "sn-gn-bd":
                    user_id = (user['surName'].upper() + '-' +
                               user['givenName'].upper() + '-' + user['birthDay'])
                else:
                    user_id = user[self.identifier]
                if 'groups' in user:
                    user['groups'] = user['groups'].upper()
                if 'classes' not in user:
                    user['classes'] = ''
                user['classes'] = user['classes'].upper()
                user_id = user_id.replace(' ', '_')
                self.import_list[user_id] = user
        if self.debug:
            print("All user in the list:")
            print(self.import_list)

    def check_attributes(self, user, line_count):
        # Check if all required attributes are there. If not ignore the line.
        if 'surName' not in user or 'givenName' not in user:
            self.log_error('Missing required attributes in line {0}.'.format(line_count))
            if self.debug:
                print('Missing required attributes in line {0}.'.format(line_count))
            return False
        if user['surName'] == "" or user['givenName'] == "":
            self.log_error('Required attributes are empty in line {0}.'.format(line_count))
            if self.debug:
                print('Required attributes are empty in line {0}.'.format(line_count))
            return False
        if self.identifier == "sn-gn-bd":
            if 'birthDay' not in user or user['birthDay'] == '':
                self.log_error('Missing birthday in line {0}.'.format(line_count))
                if self.debug:
                    print('Missing birthday in line {0}.'.format(line_count))
                return False
        elif self.identifier not in user:
            self.log_error('The line {0} does not contains the identifier {1}'.format(
                line_count, self.identifier))
            if self.debug:
                print('The line {0} does not contains the identifier {1}'.format(
                    line_count, self.identifier))
            return False
        return True

    # -- logging ------------------------------------------------------------

    def log_debug(self, text, obj):
        if self.debug:
            print(text)
            print(obj)

    def prep_log_head(self):
        if len(self.logs) == 0:
            self.logs.append('<table><caption>Statistic</caption>\n')
            self.logs.append("<tr><td>New Users</td><td>{0}</td></tr>\n".format(len(self.new_users)))
            self.logs.append("<tr><td>Deleted Users</td><td>{0}</td></tr>\n".format(len(self.del_users)))
            self.logs.append("<tr><td>Moved Users</td><td>{0}</td></tr>\n".format(len(self.moved_users)))
            self.logs.append("<tr><td>Moved Users</td><td>{0}</td></tr>\n".format(len(self.stand_users)))
            self.logs.append("<tr><td>New Groups</td><td>{0}</td></tr>\n".format(len(self.new_groups)))
            self.logs.append("<tr><td>Deleted Groups</td><td>{0}</td></tr>\n".format(len(self.del_groups)))
            self.logs.append("</table>\n")
            self.logs.append('<table><caption>Import Log</caption>\n')
            self.logs.append("</table>\n")
        else:
            self.logs[1] = "<tr><td>New Users</td><td>{0}</td></tr>\n".format(len(self.new_users))
            self.logs[2] = "<tr><td>Deleted Users</td><td>{0}</td></tr>\n".format(len(self.del_users))
            self.logs[3] = "<tr><td>Moved Users</td><td>{0}</td></tr>\n".format(len(self.moved_users))
            self.logs[4] = "<tr><td>Standing Users</td><td>{0}</td></tr>\n".format(len(self.stand_users))
            self.logs[5] = "<tr><td>New Groups</td><td>{0}</td></tr>\n".format(len(self.new_groups))
            self.logs[6] = "<tr><td>Deleted Groups</td><td>{0}</td></tr>\n".format(len(self.del_groups))

    def _write_log(self):
        if not self.import_dir:
            return
        with open(self.import_dir + '/import.log', 'w') as output:
            output.writelines(self.logs)

    def log_error(self, msg):
        self.prep_log_head()
        self.logs.insert(9, print_error(msg))
        self.logs.append("</table></body></html>\n")
        self._write_log()

    def log_msg(self, title, msg):
        self.prep_log_head()
        self.logs.insert(9, print_msg(title, msg))
        self._write_log()

    # -- API operations -----------------------------------------------------

    def add_group(self, name):
        group = {
            'name': name.upper(),
            'groupType': 'workgroup',
            'description': name,
        }
        result = self.client.add_group(group)
        if self.debug:
            print(result)
        if result.ok:
            self.all_groups.append(name.upper())
            return True
        self.log_error(result.value)
        return False

    def add_class(self, name):
        group = {
            'name': name.upper(),
            'groupType': 'class',
            # TODO translation
            'description': 'Klasse ' + name,
        }
        result = self.client.add_group(group)
        self.existing_classes.append(name)
        if self.debug:
            print(result)
        if result.ok:
            return True
        self.log_error(result.value)
        return False

    def add_user(self, user, ident):
        local_password = ""
        if self.mustChange:
            user['mustChange'] = True
        if self.password != "":
            local_password = self.password
        if self.appendBirthdayToPassword:
            local_password = local_password + user['birthDay']
        if self.appendClassToPassword:
            classes = user['classes'].split()
            if len(classes) > 0:
                local_password = local_password + classes[0]
        if local_password != "":
            user['password'] = local_password
        # The group attribute must not be part of the user json.
        if 'group' in user:
            user.pop('group')
        # Set default file system quota.
        if 'fsQuota' not in user:
            if self.role == 'teachers':
                user['fsQuota'] = self.fsTeacherQuota
            elif self.role == 'sysadmins':
                user['fsQuota'] = 0
            else:
                user['fsQuota'] = self.fsQuota
        # Set default mail system quota.
        if 'msQuota' not in user:
            if self.role == 'teachers':
                user['msQuota'] = self.msTeacherQuota
            elif self.role == 'sysadmins':
                user['msQuota'] = -1
            else:
                user['msQuota'] = self.msQuota
        result = self.client.add_user(user)
        if self.debug:
            print(result)
        if result.ok:
            self.import_list[ident]['id'] = result.object_id
            self.import_list[ident]['uid'] = result.parameters[0]
            self.import_list[ident]['password'] = result.parameters[3]
            return True
        self.log_error(result.value)
        return False

    def modify_user(self, user, ident):
        if self.identifier != 'sn-gn-bd':
            user['givenName'] = self.import_list[ident]['givenName']
            user['surName'] = self.import_list[ident]['surName']
            user['birthDay'] = self.import_list[ident]['birthDay']
        result = self.client.modify_user(user)
        if self.debug:
            print(result)
        if not result.ok:
            self.log_error(result.value)

    def move_user(self, uid, old_classes, new_classes):
        if not self.cleanClassDirs and self.role == 'students':
            if len(old_classes) > 0 and len(new_classes) > 0 and old_classes[0] != new_classes[0]:
                cmd = '/usr/share/cranix/tools/move_user_class_files.sh "{0}" "{1}" "{2}"'.format(
                    uid, old_classes[0], new_classes[0])
                if self.debug:
                    print(cmd)
                result = os.popen(cmd).read()
                if self.debug:
                    print(result)

        for group in old_classes:
            if group == '' or group.isspace():
                continue
            if group not in new_classes:
                if self.debug:
                    print("Remove user {0} from group {1}".format(uid, group))
                self.client.remove_member(group, uid)
        for group in new_classes:
            if group == '' or group.isspace():
                continue
            if group not in old_classes:
                if self.debug:
                    print("Add user {0} to group {1}".format(uid, group))
                self.client.add_member(group, uid)

    def delete_user(self, uid):
        if self.debug:
            print("Delete user {0}".format(uid))
        self.client.delete_user(uid)

    def delete_class(self, group):
        if self.debug:
            print("Delete class {0}".format(group))
        self.client.delete_group(group)

    def write_user_list(self):
        file_name = '{0}/all-{1}.txt'.format(self.import_dir, self.role)
        with open(file_name, 'w') as handle:
            # TODO Translate header
            handle.write(';'.join(user_attributes) + "\n")
            for ident in self.import_list:
                line = []
                for attr in user_attributes:
                    line.append(self.import_list[ident].get(attr, ""))
                handle.write(';'.join(map(str, line)) + "\n")
        if self.role == 'students':
            class_files = {}
            for cl in self.existing_classes:
                try:
                    class_files[cl] = open('{0}/class-{1}.txt'.format(self.import_dir, cl), 'w')
                    class_files[cl].write(';'.join(user_attributes) + "\n")
                except Exception:
                    self.log_error("Can not open:" + '{0}/class-{1}.txt'.format(self.import_dir, cl))
            for ident in self.import_list:
                user = self.import_list[ident]
                line = []
                for attr in user_attributes:
                    line.append(user.get(attr, ""))
                for user_class in user['classes'].split():
                    if user_class in class_files:
                        class_files[user_class].write(';'.join(map(str, line)) + "\n")
            for cl in class_files:
                class_files[cl].close()

        # Now we start to write the password files.
        os.system('/usr/share/cranix/tools/create_password_files.py {0} {1}'.format(
            self.import_dir, self.role))

        # Now we handle AdHocRooms.
        if self.class_adhoc and self.role == 'students':
            self.client.patch("users/moveStudentsDevices")

    # -- finish -------------------------------------------------------------

    def close(self):
        if self.check_pw:
            self.client.set_configuration("CHECK_PASSWORD_QUALITY", "yes")
        else:
            self.client.set_configuration("CHECK_PASSWORD_QUALITY", "no")
        if os.path.isfile(self.lockfile):
            os.remove(self.lockfile)
        self.log_msg("Import finished", "OK")

    def close_on_error(self, msg):
        if self.check_pw:
            self.client.set_configuration("CHECK_PASSWORD_QUALITY", "yes")
        else:
            self.client.set_configuration("CHECK_PASSWORD_QUALITY", "no")
        if os.path.isfile(self.lockfile):
            os.remove(self.lockfile)
        self.log_error(msg)
        self.log_msg("Import finished", "ERROR")
        sys.exit(1)

    # -- orchestration ------------------------------------------------------

    def run(self):
        args = self.args
        # First we remove students which have left the school.
        if args.full and args.role == 'students':
            for ident in self.all_users:
                if ident not in self.import_list and self.all_users[ident]['uid'] not in self.protected_users:
                    self.del_users.add(ident)
                    self.log_msg(ident, "User will be deleted")
                    if not args.test:
                        self.delete_user(self.all_users[ident]['uid'])

        # Now we process the user list.
        for ident in self.import_list:
            old_user = {}
            new_user = self.import_list[ident]
            new_user['role'] = args.role
            old_classes = []
            new_classes = []
            if new_user['classes'].upper() == 'ALL':
                new_classes = self.existing_classes
            else:
                new_classes = new_user['classes'].split()
            if ident in self.all_users:
                # It is an old user.
                old_user = self.all_users[ident]
                self.log_debug("Old user", old_user)
                new_user['id'] = old_user['id']
                new_user['uid'] = old_user['uid']
                old_classes = old_user['classes'].split(',')
                if old_user['classes'] != new_user['classes']:
                    self.moved_users.add(ident)
                else:
                    self.stand_users.add(ident)
                self.log_debug("Old user", old_user)
                self.log_msg(ident, "Old user. Old classes: " + old_user['classes'] +
                             " New Classes:" + new_user['classes'])
                if not args.test:
                    if args.resetPassword:
                        password = args.password
                        if 'password' in self.import_list[ident]:
                            password = self.import_list[ident]['password']
                        if password == "":
                            password = create_secure_pw(8)
                        if args.appendBirthdayToPassword:
                            password = password + old_user['birthDay']
                        if args.appendClassToPassword and len(new_classes) > 0:
                            password = password + new_classes[0]
                        old_user['password'] = password
                        self.import_list[ident]['password'] = password
                        old_user['mustChange'] = args.mustChange
                    self.modify_user(old_user, ident)
            else:
                self.new_users.add(ident)
                self.log_debug("New user", new_user)
                self.log_msg(ident, "New user. Classes:" + new_user['classes'])
                if not args.test:
                    if not self.add_user(new_user, ident):
                        continue
                else:
                    # Test if uid and password are ok if given.
                    if 'uid' in new_user:
                        res = check_uid(new_user['uid'])
                        if len(res) > 0:
                            self.log_error(res)
                    if 'password' in new_user and new_user['password'] != "":
                        res = check_password(new_user['password'])
                        if len(res) > 0:
                            self.log_error(res)

            # Process classes.
            for cl in new_classes:
                if cl == '' or cl.isspace():
                    continue
                self.log_debug("  Class:", cl)
                if cl not in self.required_classes:
                    self.required_classes.append(cl)
                if cl not in self.existing_classes:
                    self.new_groups.add(cl)
                    self.log_msg(cl, "New class")
                    if not args.test:
                        self.add_class(cl)
            if not args.test:
                self.move_user(new_user['uid'], old_classes, new_classes)
            # Process groups.
            if 'group' in self.import_list[ident]:
                for gr in self.import_list[ident]['group'].split():
                    if gr.upper() not in self.all_groups:
                        self.new_groups.add(gr)
                        self.log_msg(gr, "New group")
                        if not args.test:
                            self.add_group(gr)
                    self.log_msg(gr, "Add user to group")
                    if not args.test:
                        self.client.add_member(gr, new_user['uid'])

        # Now we write the user list.
        if args.debug:
            print('Resulted user list')
            print(self.import_list)
        if not args.test:
            self.write_user_list()

        if not args.test and args.cleanClassDirs:
            for c in self.existing_classes:
                os.system('/usr/sbin/crx_clean_group_directory.sh "{0}"'.format(c.upper()))

        if args.allClasses:
            for c in self.existing_classes:
                if c not in self.required_classes:
                    self.log_msg(c, "Class will be deleted")
                    self.del_groups.add(c)
                    if not args.test:
                        self.delete_class(c)
            self.read_classes()

        self.close()


def build_parser(roles=None):
    parser = ArgumentParser()
    # String parameter
    parser.add_argument("--input", dest="input", default="/tmp/userlist.txt",
                        help="The import file with full path.")
    parser.add_argument("--role", dest="role", default="students",
                        choices=roles or DEFAULT_ROLES,
                        help="Role of the users to import: students|teachers|administration")
    parser.add_argument("--password", dest="password", default="",
                        help="Default value for password.")
    parser.add_argument("--lang", dest="lang", default="DE",
                        help="Language of the header.")
    parser.add_argument("--identifier", dest="identifier", default="sn-gn-bd",
                        choices=['sn-gn-bd', 'uid', 'uuid'],
                        help="Which attribute(s) will be used to identify an user. "
                             "Normaly the sn givenName and birthday combination will be used "
                             "(sn-gn-bd). Possible values are uid or uuid (uniqueidentifier).")
    # Boolean parameter
    parser.add_argument("--full", dest="full", default=False, action="store_true",
                        help="List is a full list. User which are not in the list will be removed. "
                             "This parameter has only effect if role == 'students'.")
    parser.add_argument("--test", dest="test", default=False, action="store_true",
                        help="If this parameter is true no changes will be done. The scipt only "
                             "reports what would happends.")
    parser.add_argument("--debug", dest="debug", default=False, action="store_true",
                        help="Run in debug mode.")
    parser.add_argument("--mustChange", dest="mustChange", default=False, action="store_true",
                        help="If set, the new users must change its password by the first login.")
    parser.add_argument("--resetPassword", dest="resetPassword", default=False, action="store_true",
                        help="If this option is true the password of old user will be reseted too.")
    parser.add_argument("--allClasses", dest="allClasses", default=False, action="store_true",
                        help="The import list contains all classes. Classes which are not in the "
                             "list will be deleted. This parameter has only affect when role=students.")
    parser.add_argument("--appendBirthdayToPassword", dest="appendBirthdayToPassword",
                        default=False, action="store_true",
                        help="Append the birthday of a user to the password.")
    parser.add_argument("--appendClassToPassword", dest="appendClassToPassword",
                        default=False, action="store_true",
                        help="Append the upper case name of the first class of a user to the password.")
    parser.add_argument("--cleanClassDirs", dest="cleanClassDirs", default=False,
                        action="store_true",
                        help="Remove the content of the directories of the classes. This parameter "
                             "has only affect when role=students.")
    return parser


def main(argv=None):
    client = api.CrxApi()
    parser = build_parser(get_roles(client))
    args = parser.parse_args(argv)
    importer = Importer(args, client=client)
    importer.init()
    importer.run()
    return importer


if __name__ == "__main__":
    main()