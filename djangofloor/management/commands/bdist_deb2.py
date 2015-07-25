# -*- coding: utf-8 -*-
from __future__ import unicode_literals, print_function, absolute_import
import codecs
import os
import re
import sys

from django.core.management import execute_from_command_line
from django.template.loader import render_to_string
# noinspection PyPackageRequirements
from stdeb import util
# noinspection PyPackageRequirements
from stdeb.command.sdist_dsc import sdist_dsc

from djangofloor.scripts import set_env

try:
    # Python 2.x
    import ConfigParser
except ImportError:
    # Python 3.x
    # noinspection PyPep8Naming
    import configparser as ConfigParser

__author__ = 'Matthieu Gallet'


class BdistDeb2(sdist_dsc):
    description = "distutils command to create a Debian Django package"

    def run(self):
        """Order of operations:

            * create the source package with `sdist_dsc`
            * update the Python dependencies
            * run specific DjangoFloor command for extra Debian files (systemd, static files, …)
            * add postinstall files
            * build  a .deb package from the modified `sdist_dsc`
        """
        # generate .dsc source pkg
        sdist_dsc.run(self)
        project_name = self.distribution.metadata.name
        # get relevant options passed to sdist_dsc
        # sdist_dsc = self.get_finalized_command('sdist_dsc')
        dsc_tree = self.dist_dir
        # execute system command and read output (execute and read output of find cmd)
        target_dirs = []
        for entry in os.listdir(dsc_tree):
            fulldir = os.path.join(dsc_tree, entry)
            if os.path.isdir(fulldir):
                if entry == 'tmp_py2dsc':
                    continue
                target_dirs.append(fulldir)
        if len(target_dirs) > 1:
            raise ValueError('More than one directory in deb_dist. '
                             'Unsure which is source directory. All: %r' % (target_dirs,))
        elif len(target_dirs) == 0:
            raise ValueError('could not find debian source directory')
        target_dir = target_dirs[0]

        stdeb_config = ConfigParser.ConfigParser()
        stdeb_config.read(['stdeb.cfg'])

        extra_processes = []
        if stdeb_config.has_option('djangofloor', 'processes'):
            extra_processes = []
            for process_line in stdeb_config.get('djangofloor', 'processes').splitlines():
                process_line = process_line.strip()
                process_name, sep, process_cmd = process_line.partition(':')
                if process_line and sep != ':':
                    print('Extra processes must be of the form "process_name:command_line"')
                    raise ValueError
                elif process_line:
                    extra_processes.append(process_line)
        frontend = None
        if stdeb_config.has_option('djangofloor', 'frontend'):
            frontend = stdeb_config.get('djangofloor', 'frontend')
        process_manager = None
        if stdeb_config.has_option('djangofloor', 'process_manager'):
            process_manager = stdeb_config.get('djangofloor', 'process_manager')
        username = project_name
        if stdeb_config.has_option('djangofloor', 'username'):
            username = stdeb_config.get('djangofloor', 'username')

        # prepare the use of the gen_install command
        os.environ['DJANGOFLOOR_PROJECT_NAME'] = project_name
        set_env()
        collect_static_dir = os.path.join(target_dir, 'gen_install', 'var', project_name, 'static')
        etc_dir = os.path.join(target_dir, 'gen_install', 'etc')
        gen_install_command = [sys.argv[0], 'gen_install', '--collectstatic', collect_static_dir]
        gen_install_command += ['--user', username]
        for extra_process in extra_processes:
            gen_install_command += ['--extra-process', extra_process]
        if frontend == 'nginx':
            gen_install_command += ['--nginx', os.path.join(etc_dir, 'nginx', 'sites-available', '%s.conf' % project_name)]
        elif frontend == 'apache':
            gen_install_command += ['--apache', os.path.join(etc_dir, 'apache2', 'sites-available', '%s.conf' % project_name)]
        elif frontend is not None:
            print('Invalid value for frontend: %s' % frontend)
            raise ValueError
        gen_install_command += ['--conf', os.path.join(etc_dir, project_name)]
        if process_manager == 'supervisor':
            gen_install_command += ['--supervisor', os.path.join(etc_dir, 'supervisor.d', '%s.conf' % project_name)]
        elif process_manager == 'systemd':
            gen_install_command += ['--systemd', os.path.join(etc_dir, 'systemd', 'system')]
        elif process_manager is not None:
            print('Invalid value for process manager: %s' % process_manager)
            raise ValueError
        execute_from_command_line(gen_install_command)
        # add the copy of these new files to the Makefile
        extra_lines = ['\trsync -av gen_install/ %(root)s/']

        # todo : ajouter Apache/nginx/systemd/supervisor en dépendance
        with codecs.open(os.path.join(target_dir, 'debian/control'), 'r', encoding='utf-8') as control_fd:
            control = control_fd.read()
        old_depends = '${misc:Depends}, ${python:Depends}'
        if stdeb_config.has_option('DEFAULT', 'depends'):
            new_depends = stdeb_config.get('DEFAULT', 'depends')
        else:
            new_depends = old_depends
        if process_manager == 'supervisor':
            new_depends += ', supervisor'
        elif process_manager == 'systemd':
            new_depends += ', systemd'
        if frontend == 'apache':
            new_depends += ', apache2'
        elif frontend == 'nginx':
            new_depends += ', nginx'
        control = control.replace(old_depends, new_depends)
        with codecs.open(os.path.join(target_dir, 'debian/control'), 'w', encoding='utf-8') as control_fd:
            control_fd.write(control)

        # rewrite rules file to append djangofloor extra info
        rules_filename = os.path.join(target_dir, 'debian', 'rules')
        new_rules_content = ''
        python2_re = re.compile(r'^\s*python setup.py install --force --root=debian/([^/\s]+) .*$')
        python3_re = re.compile(r'^\s*python3 setup.py install --force --root=debian/([^/\s]+) .*$')
        debian_names = {}
        with codecs.open(rules_filename, 'r', encoding='utf-8') as rules_fd:
            for line in rules_fd:
                new_rules_content += line
                for python_version, python_re in ((2, python2_re), (3, python3_re)):
                    matcher = python_re.match(line)
                    if matcher:
                        debian_name = matcher.group(1)
                        debian_names[python_version] = debian_name
                        values = {'root': 'debian/%s' % debian_name, 'project_name': project_name, }
                        for extra_line in extra_lines:
                            new_rules_content += (extra_line % values) + '\n'
        with codecs.open(rules_filename, 'w', encoding='utf-8') as rules_fd:
            rules_fd.write(new_rules_content)

        values = {'project_name': project_name}
        for python_version in (2, 3):
            if python_version not in debian_names:
                continue
            values.update({'python_version': python_version, 'debian_name': debian_names[python_version]})
            python_postinst = os.path.join(target_dir, 'debian', debian_names[python_version] + '.postinst')
            with codecs.open(python_postinst, 'w', encoding='utf-8') as postinst_fd:
                content = render_to_string('djangofloor/commands/deb_postinst.sh', values)
                postinst_fd.write(content)

        syscmd = ['dpkg-buildpackage', '-rfakeroot', '-uc', '-b']
        util.process_command(syscmd, cwd=target_dir)
