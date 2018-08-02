from configparser import ConfigParser
from email import message_from_string

import pkg_resources

project_name = "{{ DF_MODULE_NAME }}"
vagrant_tmp_dir = "{{ tmp_dir.1 }}"
vagrant_install_dir = "{{ install_dir.1 }}"
vagrant_config_filename = "{{ fpm_project_config_filename.1 }}"


def main():
    project_distribution = pkg_resources.get_distribution(project_name)
    parser = ConfigParser()
    # analyze scripts to detect which processes to launch on startup
    entry_map = pkg_resources.get_entry_map(project_name)
    parser.add_section("processes")
    for script_name, entry_point in entry_map.get("console_scripts").items():
        script_value = entry_point.module_name
        if entry_point.attrs:
            script_value += ":%s" % entry_point.attrs[:1]
        if entry_point.extras:
            script_value += " %s" % entry_point.extras[:1]
        parser.set("processes", script_name, script_value)

    defaults = {"version": project_distribution.version, "name": project_name}
    maintainer = [None, None]
    # noinspection PyBroadException
    pkg_info = project_distribution.get_metadata("PKG-INFO")
    msg = message_from_string(pkg_info)
    for k, v in msg.items():
        if v == "UNKNOWN":
            continue
        elif k == "License":
            defaults["license"] = v
        elif k == "Description":
            defaults["description"] = v
        elif k == "Home-page":
            defaults["url"] = v
        elif k == "Author":
            maintainer[0] = v
        elif k == "Author-email":
            maintainer[1] = v
    if maintainer[0] and maintainer[1]:
        defaults["maintainer"] = "%s <%s>" % tuple(maintainer)
        defaults["vendor"] = "%s <%s>" % tuple(maintainer)

    parser["deb"] = defaults
    parser["rpm"] = defaults
    parser["tar"] = defaults
    with open(vagrant_config_filename, "w", encoding="utf-8") as fd:
        parser.write(fd)


if __name__ == "__main__":
    main()
