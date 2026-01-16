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

    logger.debug(add_group)
    logger.debug(result)

    if result['code'] == 'OK':
        all_groups.append(name.upper())
        return True
    else:
        logger.error(result['value'])
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

    logger.debug(result)

    if result['code'] == 'OK':
        return True
    else:
        logger.error(result['value'])
        return False

def delete_class(group):
    cmd = '/usr/sbin/crx_api_text.sh DELETE "groups/text/{0}"'.format(group)
    logger.debug(cmd)
    result = os.popen(cmd).read()
    logger.debug(result)

def read_classes():

    classes = []
    for group in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/class').readlines():
        classes.append(group.strip().upper())
        logger.debug(f'Classes: {classes}')
    return classes

def read_groups():

    groups = []
    for group in os.popen('/usr/sbin/crx_api_text.sh GET groups/text/byType/workgroups').readlines():
        groups.append(group.strip().upper())
        logger.debug(f'Groups: {groups}')
    return groups

