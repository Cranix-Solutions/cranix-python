import time

from typing import Set
from configobj import ConfigObj

from . import _user_import

from ._vars import user_attributes

from ._functions import (print_error,
                         print_msg)

from ._init_functions import *

# Internal debug only
init_debug = False

# Define some global variables
logs = []
required_classes = []
existing_classes = []
protected_users  = []
all_groups       = []
all_users   = {}
import_list = {}
new_user_count  = 1
new_group_count = 1
lockfile = '/run/crx_import_user'

new_users: Set[str] = set([])
new_groups: Set[str] = set([])
del_users: Set[str] = set([])
del_groups: Set[str] = set([])
moved_users: Set[str] = set([])
stand_users: Set[str] = set([])

date = time.strftime("%Y-%m-%d.%H-%M-%S")
# read and set some default values
config    = ConfigObj("/opt/cranix-java/conf/cranix-api.properties",list_values=False)
passwd    = config['de.cranix.dao.User.Register.Password']
protected_users = config['de.cranix.dao.User.protected'].split(",")
domain    = os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/DOMAIN').read()
home_base = os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/HOME_BASE').read()
check_pw  = os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/CHECK_PASSWORD_QUALITY').read().lower() == 'yes'
class_adhoc = os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/MAINTAIN_ADHOC_ROOM_FOR_CLASSES').read().lower() == 'yes'
roles  = []
for role in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/primary').readlines():
  roles.append(role.strip())



"""-----------------------SOME FUNCTIONS ARE NOW THERE SO THEY CAN BE USED IN INIT FUNCTION--------------------------"""
"""--------AS SOON AS THE GLOBAL VARIABLES WILL BE REMOVED THIS FUNCTIONS CAN BE MOVED TO _init_functions.py---------"""



def prep_log_head():
    global new_users, del_users, moved_users, stand_users, new_groups, del_groups
    if len(logs) == 0:
        logs.append('<table><caption>Statistic</caption>\n')
        logs.append("<tr><td>New Users</td><td>{0}</td></tr>\n".format(len(new_users)))
        logs.append("<tr><td>Deleted Users</td><td>{0}</td></tr>\n".format(len(del_users)))
        logs.append("<tr><td>Moved Users</td><td>{0}</td></tr>\n".format(len(moved_users)))
        logs.append("<tr><td>Moved Users</td><td>{0}</td></tr>\n".format(len(stand_users)))
        logs.append("<tr><td>New Groups</td><td>{0}</td></tr>\n".format(len(new_groups)))
        logs.append("<tr><td>Deleted Groups</td><td>{0}</td></tr>\n".format(len(del_groups)))
        logs.append("</table>\n")
        logs.append('<table><caption>Import Log</caption>\n')
        logs.append("</table>\n")
    else:
        logs[1] = "<tr><td>New Users</td><td>{0}</td></tr>\n".format(len(new_users))
        logs[2] = "<tr><td>Deleted Users</td><td>{0}</td></tr>\n".format(len(del_users))
        logs[3] = "<tr><td>Moved Users</td><td>{0}</td></tr>\n".format(len(moved_users))
        logs[4] = "<tr><td>Standing Users</td><td>{0}</td></tr>\n".format(len(stand_users))
        logs[5] = "<tr><td>New Groups</td><td>{0}</td></tr>\n".format(len(new_groups))
        logs[6] = "<tr><td>Deleted Groups</td><td>{0}</td></tr>\n".format(len(del_groups))

def log_error(msg):
    global logs
    prep_log_head()
    logs.insert(9,print_error(msg))
    logs.append("</table></body></html>\n")
    with open(import_dir + '/import.log','w') as output:
        output.writelines(logs)

def log_msg(title,msg):
    global logs
    prep_log_head()
    logs.insert(9,print_msg(title, msg))
    with open(import_dir + '/import.log','w') as output:
        output.writelines(logs)

def add_group(name):
    global new_group_count
    global all_groups
    group = {}
    group['name'] = name.upper()
    group['groupType'] = 'workgroup'
    group['description'] = name
    file_name = '{0}/tmp/group_add.{1}'.format(import_dir,new_group_count)
    with open(file_name, 'w') as fp:
        json.dump(group, fp, ensure_ascii=False)
    result = json.load(os.popen('/usr/sbin/crx_api_post_file.sh groups/add ' + file_name))
    new_group_count = new_group_count + 1
    if debug:
        print(add_group)
        print(result)
    if result['code'] == 'OK':
        all_groups.append(name.upper())
        return True
    else:
        log_error(result['value'])
        return False

def add_class(name):
    global new_group_count
    global existing_classes
    group = {}
    group['name'] = name.upper()
    group['groupType'] = 'class'
    #TODO translation
    group['description'] ='Klasse ' + name
    file_name = '{0}/tmp/group_add.{1}'.format(import_dir,new_group_count)
    with open(file_name, 'w') as fp:
        json.dump(group, fp, ensure_ascii=False)
    result = json.load(os.popen('/usr/sbin/crx_api_post_file.sh groups/add ' + file_name))
    existing_classes.append(name)
    new_group_count = new_group_count + 1
    if debug:
        print(result)
    if result['code'] == 'OK':
        return True
    else:
        log_error(result['value'])
        return False

def add_user(user,ident):
    global password
    global new_user_count
    global import_list
    local_password = ""
    if mustChange:
        user['mustChange'] = True
    if password != "":
        local_password = password
    if appendBirthdayToPassword:
        local_password = local_password + user['birthDay']
    if appendClassToPassword:
        classes = user['classes'].split()
        if len(classes) > 0:
            local_password = local_password + classes[0]
    if local_password != "":
        user['password'] = local_password
    # The group attribute must not be part of the user json
    if 'group' in user:
        user.pop('group')
    #if 'class' in user:
    #    user['classes'] = user['class']
    #    del user['class']
    #Set default file system quota
    if not 'fsQuota' in user:
        if role == 'teachers':
            user['fsQuota'] = fsTeacherQuota
        elif role == 'sysadmins':
            user['fsQuota'] = 0
        else:
            user['fsQuota'] = fsQuota
    #Set default mail system quota
    if not 'msQuota' in user:
        if role == 'teachers':
            user['msQuota'] = msTeacherQuota
        elif role == 'sysadmins':
            user['msQuota'] = -1
        else:
            user['msQuota'] = msQuota
    file_name = '{0}/tmp/user_add.{1}'.format(import_dir,new_user_count)
    with open(file_name, 'w') as fp:
        json.dump(user, fp, ensure_ascii=False)
    result = json.load(os.popen('/usr/sbin/crx_api_post_file.sh users/insert ' + file_name))
    if debug:
        print(result)
    if result['code'] == 'OK':
        import_list[ident]['id']       = result['objectId']
        import_list[ident]['uid']      = result['parameters'][0]
        import_list[ident]['password'] = result['parameters'][3]
        new_user_count = new_user_count + 1
        return True
    else:
        log_error(result['value'])
        return False

def modify_user(user,ident):
    if identifier != 'sn-gn-bd':
        user['givenName'] = import_list[ident]['givenName']
        user['surName']   = import_list[ident]['surName']
        user['birthDay']  = import_list[ident]['birthDay']
    file_name = '{0}/tmp/user_modify.{1}'.format(import_dir,user['uid'])
    with open(file_name, 'w') as fp:
        json.dump(user, fp, ensure_ascii=False)
    result = json.load(os.popen('/usr/sbin/crx_api_post_file.sh users/{0} "{1}" '.format(user['id'],file_name)))
    if debug:
        print(result)
    if result['code'] == 'ERROR':
        log_error(result['value'])

def move_user(uid,old_classes,new_classes):
    if not cleanClassDirs and role == 'students':
        if len(old_classes) > 0 and len(new_classes) > 0 and old_classes[0] != new_classes[0]:
            cmd = '/usr/share/cranix/tools/move_user_class_files.sh "{0}" "{1}" "{2}"'.format(uid,old_classes[0],new_classes[0])
            if debug:
                print(cmd)
            result = os.popen(cmd).read()
            if debug:
                print(result)

    for g in old_classes:
       if g == '' or g.isspace():
            continue
       if not g in new_classes:
           cmd = '/usr/sbin/crx_api_text.sh DELETE "users/text/{0}/groups/{1}"'.format(uid,g)
           if debug:
               print(cmd)
           result = os.popen(cmd).read()
           if debug:
               print(result)
    for g in new_classes:
       if g == '' or g.isspace():
            continue
       if not g in old_classes:
           cmd = '/usr/sbin/crx_api_text.sh PUT "users/text/{0}/groups/{1}"'.format(uid,g)
           if debug:
               print(cmd)
           result = os.popen(cmd).read()
           if debug:
               print(result)

def delete_user(uid):
    cmd = '/usr/sbin/crx_api_text.sh DELETE "users/text/{0}"'.format(uid)
    if debug:
        print(cmd)
    result = os.popen(cmd).read()
    if debug:
        print(result)

def delete_class(group):
    cmd = '/usr/sbin/crx_api_text.sh DELETE "groups/text/{0}"'.format(group)
    if debug:
        print(cmd)
    result = os.popen(cmd).read()
    if debug:
        print(result)

def _write_user_list():
    file_name = '{0}/all-{1}.txt'.format(import_dir,role)
    with open(file_name, 'w') as fp:
        #TODO Translate header
        fp.write(';'.join(user_attributes)+"\n")
        for ident in import_list:
            line = []
            for attr in user_attributes:
                line.append(import_list[ident].get(attr,""))
            fp.write(';'.join(map(str,line))+"\n")
    if role == 'students':
        class_files = {}
        for cl in existing_classes:
            try:
                class_files[cl] = open('{0}/class-{1}.txt'.format(import_dir,cl),'w')
                class_files[cl].write(';'.join(user_attributes)+"\n")
            except:
                log_error("Can not open:" + '{0}/class-{1}.txt'.format(import_dir,cl))
        for ident in import_list:
            user = import_list[ident]
            line = []
            for attr in user_attributes:
                line.append(user.get(attr,""))
            for user_class in user['classes'].split():
                if user_class in class_files:
                    class_files[user_class].write(';'.join(map(str,line))+"\n")
        for cl in class_files:
            class_files[cl].close()

    #Now we start to write the password files
    os.system('/usr/share/cranix/tools/create_password_files.py {0} {1}'.format(import_dir,role))

    #Now we handle AdHocRooms:
    if class_adhoc and role == 'students':
        os.system('/usr/sbin/crx_api.sh PATCH users/moveStudentsDevices')


"""--------------------------------------------------INIT FUNCTION---------------------------------------------------"""


def init(args):
    global input_file, role, password, identifier, full, test, debug, mustChange
    global resetPassword, allClasses, cleanClassDirs, appendBirthdayToPassword, appendClassToPassword
    global import_dir, required_classes, existing_classes, all_users, import_list
    global fsQuota, fsTeacherQuota, msQuota, msTeacherQuota

    password       = ""
    fsQuota        = int(os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/FILE_QUOTA').read())
    fsTeacherQuota = int(os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/FILE_TEACHER_QUOTA').read())
    msQuota        = int(os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/MAIL_QUOTA').read())
    msTeacherQuota = int(os.popen('/usr/sbin/crx_api_text.sh GET system/configuration/MAIL_TEACHER_QUOTA').read())
    #Check if import is running
    if os.path.isfile(lockfile):
        close_on_error("Import is already running")
    os.system("/usr/sbin/crx_api.sh PUT system/configuration/CHECK_PASSWORD_QUALITY/no")
    import_dir = home_base + "/groups/SYSADMINS/userimports/" + date
    os.system('mkdir -pm 770 ' + import_dir + '/tmp' )
    #create lock file
    with open(lockfile,'w') as f:
        f.write(date)
    #write the parameter
    args_dict=args.__dict__
    args_dict["startTime"] = date
    with open(import_dir +'/parameters.json','w') as f:
        json.dump(args_dict,f,ensure_ascii=False)
    input_file               = args.input
    role                     = args.role
    password                 = args.password
    identifier               = args.identifier
    full                     = args.full
    test                     = args.test
    debug                    = args.debug
    mustChange               = args.mustChange
    resetPassword            = args.resetPassword
    allClasses               = args.allClasses
    cleanClassDirs           = args.cleanClassDirs
    appendBirthdayToPassword = args.appendBirthdayToPassword
    appendClassToPassword    = args.appendClassToPassword

    existing_classes = read_classes()
    all_groups = read_groups()
    all_users = read_users(role=role, identifier=identifier, debug=debug)
    import_list = read_csv(path=input_file, identifier="sn-gn-bd", debug=False)

    #FUCNTIONS FROM USERS IMPORT
    _user_import.remove_unnececary_students(args)
    _user_import.proceed_the_user_list(args)
    _user_import.write_user_list(args)
    _user_import.delete_unnecessary_classes(args)