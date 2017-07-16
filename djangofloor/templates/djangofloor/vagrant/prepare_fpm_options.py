from configparser import ConfigParser

import pkg_resources

project_name = '{{ DF_MODULE_NAME }}'
vagrant_tmp_dir = '{{ tmp_dir.1 }}'
vagrant_install_dir = '{{ install_dir.1 }}'


def main():
    project_distribution = pkg_resources.get_distribution(project_name)
    parser = ConfigParser()
    # analyze scripts to detect which processes to launch on startup
    entry_map = pkg_resources.get_entry_map(project_name)
    parser.add_section('processes')
    for script_name, entry_point in entry_map.get('console_scripts').items():
        script_value = entry_point.module_name
        if entry_point.attrs:
            script_value += ':%s' % entry_point.attrs[:1]
        if entry_point.extras:
            script_value += ' %s' % entry_point.extras[:1]
        parser.set('processes', script_name, script_value)

    defaults = {'version': project_distribution.version, 'name': project_name}
    maintainer = [None, None]
    # noinspection PyBroadException
    try:
        for line in project_distribution.get_metadata_lines('PKG-INFO'):
            k, sep, v = line.partition(': ')
            if v == 'UNKNOWN' or sep != ': ':
                continue
            elif k == 'License':
                defaults['license'] = v
            elif k == 'Description':
                defaults['description'] = v
            elif k == 'Home-page':
                defaults['url'] = v
            elif k == 'Author':
                maintainer[0] = v
            elif k == 'Author-email':
                maintainer[1] = v
    except:
        pass
    if maintainer[0] and maintainer[1]:
        defaults['maintainer'] = '%s <%s>' % tuple(maintainer)
    parser['DEFAULT'] = defaults
    with open('{{ fpm_config_filename.1 }}', 'w', encoding='utf-8') as fd:
        parser.write(fd)


if __name__ == '__main__':
    main()
