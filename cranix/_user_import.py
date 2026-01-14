from _init_functions import *
from .__init__ import (log_error,
                       log_msg,
                       add_group,
                       add_class,
                       add_user,
                       modify_user,
                       move_user,
                       delete_user,
                       delete_class)

def remove_unnececary_students(args):

    if args.full and args.role == 'students':
        for ident in all_users:
            if not ident in import_list and not all_users[ident]['uid'] in protected_users:
                del_users.add(ident)
                log_msg(ident, "User will be deleted")
                if not args.test:
                    delete_user(all_users[ident]['uid'])

def proceed_the_user_list(args):

    for ident in import_list:
        # First we proceed the classes

        old_user = {}
        new_user = import_list[ident]
        new_user['role'] = args.role
        old_classes = []
        new_classes = []

        if new_user['classes'].upper() == 'ALL':
            new_classes = existing_classes
        else:
            new_classes = new_user['classes'].split()

        if ident in all_users:

            # It is an old user

            old_user = all_users[ident]
            log_debug("Old user", old_user)
            new_user['id'] = old_user['id']
            new_user['uid'] = old_user['uid']
            old_classes = old_user['classes'].split(',')

            if old_user['classes'] != new_user['classes']:
                moved_users.add(ident)
            else:
                stand_users.add(ident)

            log_debug("Old user", old_user)
            log_msg(ident, "Old user. Old classes: " + old_user['classes'] + " New Classes:" + new_user['classes'])

            if not args.test:
                if args.resetPassword:

                    password = args.password
                    if 'password' in import_list[ident]:
                        password = import_list[ident]['password']

                    if password == "":
                        password = create_secure_pw(8)

                    if args.appendBirthdayToPassword:
                        password = password + old_user['birthDay']

                    if args.appendClassToPassword and len(new_classes) > 0:
                        password = password + new_classes[0]

                    old_user['password'] = password
                    import_list[ident]['password'] = password
                    old_user['mustChange'] = args.mustChange

                modify_user(old_user, ident)
        else:

            new_users.add(ident)
            log_debug("New user", new_user)
            log_msg(ident, "New user. Classes:" + new_user['classes'])

            if not args.test:
                if not add_user(new_user, ident):
                    continue

            else:
                # Test if uid and password are ok if given
                if 'uid' in new_user:
                    res = check_uid(new_user['uid'])
                    if len(res) > 0:
                        log_error(res)

                if 'password' in new_user and new_user['password'] != "":
                    res = check_password(new_user['password'])
                    if len(res) > 0:
                        log_error(res)

        # trate classes
        for cl in new_classes:
            if cl == '' or cl.isspace():
                continue
            log_debug("  Class:", cl)
            if cl not in required_classes:
                required_classes.append(cl)

            if cl not in existing_classes:
                new_groups.add(cl)
                log_msg(cl, "New class")

                if not args.test:
                    add_class(cl)

        if not args.test:
            move_user(new_user['uid'], old_classes, new_classes)

        # trate groups
        if 'group' in import_list[ident]:
            for gr in import_list[ident]['group'].split():
                if gr.upper() not in all_groups:

                    new_groups.add(gr)
                    log_msg(gr, "New group")

                    if not args.test:
                        add_group(gr)

                log_msg(gr, "Add user to group")
                if not args.test:

                    cmd = '/usr/sbin/oss_api_text.sh PUT users/text/{0}/groups/{1}'.format(new_user['uid'], gr)
                    if args.debug:
                        print(cmd)
                    result = os.popen(cmd).read()
                    if args.debug:
                        print(result)

def _write_user_list(args):

    if args.debug:

        print('Resulted user list')
        print(import_list)

    if not args.test:
        write_user_list()

    if not args.test and args.cleanClassDirs:

        for c in existing_classes:
            os.system('/usr/sbin/crx_clean_group_directory.sh "{0}"'.format(c.upper()))

def delete_unnecessary_classes(args):

    if args.allClasses:

        for c in existing_classes:
            if not c in required_classes:

                log_msg(c, "Class will be deleted")
                del_groups.add(c)

                if not args.test:
                    delete_class(c)

        read_classes()