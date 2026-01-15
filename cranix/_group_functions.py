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

def delete_class(group):
    cmd = '/usr/sbin/crx_api_text.sh DELETE "groups/text/{0}"'.format(group)
    if debug:
        print(cmd)
    result = os.popen(cmd).read()
    if debug:
        print(result)

def read_classes():

    classes = []
    for group in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/class').readlines():
        classes.append(group.strip().upper())
    return classes

def read_groups():

    groups = []
    for group in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/workgroups').readlines():
        groups.append(group.strip().upper())

    return groups

