# -*- coding: utf-8 -*-
"""Build a .deb package with binaries and default config
=====================================================

Require a `stdeb.cfg` at the root of your project.
"""
from __future__ import unicode_literals, print_function, absolute_import
import codecs
from distutils.errors import DistutilsModuleError
import os
import re
import sys

from django.core.management import execute_from_command_line
from django.template.loader import render_to_string
try:
    # noinspection PyPackageRequirements
    from stdeb import util
    # noinspection PyPackageRequirements
    from stdeb.command.sdist_dsc import sdist_dsc
except ImportError:
    util = None
    sdist_dsc = None

from djangofloor.scripts import set_env

try:
    # Python 2.x
    import ConfigParser
except ImportError:
    # Python 3.x
    # noinspection PyPep8Naming
    import configparser as ConfigParser

__author__ = 'Matthieu Gallet'


class BdistDebDjango(sdist_dsc):
    description = "distutils command to create a Debian Django package"

    def get_config_files(self):
        """ Return the list of `stdeb.cfg` paths in the same way as the `sdist_dsc` command
        :return: list of path (relative or absolute)
        :rtype: :class:`list` of :class:`str`
        """
        cfg_files = []
        if self.extra_cfg_file is not None:
            cfg_files.append(self.extra_cfg_file)
        config_fname = 'stdeb.cfg'
        # Distutils fails if not run from setup.py dir, so this is OK.
        if os.path.exists(config_fname):
            cfg_files.append(config_fname)
        use_setuptools = True
        try:
            ei_cmd = self.distribution.get_command_obj('egg_info')
        except DistutilsModuleError:
            use_setuptools = False
            ei_cmd = None
        if use_setuptools:
            self.run_command('egg_info')
            egg_info_dirname = ei_cmd.egg_info
            # Pickup old location of stdeb.cfg
            config_fname = os.path.join(egg_info_dirname, 'stdeb.cfg')
            if os.path.exists(config_fname):
                cfg_files.append(config_fname)
        else:
            entries = os.listdir(os.curdir)
            for entry in entries:
                if not (entry.endswith('.egg-info') and os.path.isdir(entry)):
                    continue
                # Pickup old location of stdeb.cfg
                config_fname = os.path.join(entry, 'stdeb.cfg')
                if os.path.exists(config_fname):
                    cfg_files.append(config_fname)
        return cfg_files

    def get_option(self, section, option, fallback=None):
        if self.config_parser.has_option(section=section, option=option):
            return self.config_parser.get(section=section, option=option)
        return fallback

    def run(self):
        """Order of operations:

            * create the source package with `sdist_dsc`
            * update the Python dependencies
            * run specific DjangoFloor command for extra Debian files (systemd, static files, …)
            * add postinstall files
            * build  a .deb package from the modified `sdist_dsc`
        """
        if sdist_dsc is None or util is None:
            self.stderr.write('Unable to load bdist_deb')
            return 1
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

        # noinspection PyAttributeOutsideInit
        self.config_parser = ConfigParser.ConfigParser()
        self.config_parser.read(self.get_config_files())

        extra_processes = []
        for process_line in self.get_option(project_name, 'processes', fallback='').splitlines():
            process_line = process_line.strip()
            process_name, sep, process_cmd = process_line.partition(':')
            if process_line and sep != ':':
                print('Extra processes must be of the form "process_name:command_line"')
                raise ValueError
            elif process_line:
                extra_processes.append(process_line)
        frontend = self.get_option(project_name, 'frontend', fallback=None)
        process_manager = self.get_option(project_name, 'process_manager', fallback=None)
        username = self.get_option(project_name, 'username', fallback=project_name)
        extra_depends = ''

        debian_project_name = project_name.replace('-', '_')
        conf_name = '%s.conf' % debian_project_name
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
            gen_install_command += ['--nginx', os.path.join(etc_dir, 'nginx', 'sites-available', conf_name)]
            extra_depends += ', nginx'
        elif frontend == 'apache2.2':
            gen_install_command += ['--apache22', os.path.join(etc_dir, 'apache2', 'sites-available', conf_name)]
            extra_depends += ', apache2 (>= 2.2)'
        elif frontend == 'apache2.4':
            gen_install_command += ['--apache24', os.path.join(etc_dir, 'apache2', 'sites-available', conf_name)]
            extra_depends += ', apache2 (>= 2.4)'
        elif frontend is not None:
            print('Invalid value for frontend: %s' % frontend)
            raise ValueError
        gen_install_command += ['--conf', os.path.join(etc_dir, debian_project_name)]
        if process_manager == 'supervisor':
            gen_install_command += ['--supervisor', os.path.join(etc_dir, 'supervisor', 'conf.d', conf_name)]
            extra_depends += ', supervisor'
        elif process_manager == 'systemd':
            gen_install_command += ['--systemd', os.path.join(etc_dir, 'systemd', 'system')]
            extra_depends += ', systemd'
        elif process_manager is not None:
            print('Invalid value for process manager: %s' % process_manager)
            raise ValueError
        execute_from_command_line(gen_install_command)
        # add the copy of these new files to the Makefile
        extra_lines = ['\trsync -av gen_install/ %(root)s/']

        # patch dependencies in control file
        with codecs.open(os.path.join(target_dir, 'debian/control'), 'r', encoding='utf-8') as control_fd:
            control = control_fd.read()
        old_depends2 = '${misc:Depends}, ${python:Depends}'
        old_depends3 = '${misc:Depends}, ${python3:Depends}'
        new_depends2 = self.get_option(project_name, 'depends', fallback=old_depends2)
        new_depends3 = self.get_option(project_name, 'depends3', fallback=old_depends3)
        control = control.replace(old_depends2, new_depends2 + extra_depends)
        control = control.replace(old_depends3, new_depends3 + extra_depends)
        with codecs.open(os.path.join(target_dir, 'debian/control'), 'w', encoding='utf-8') as control_fd:
            control_fd.write(control)

        # rewrite rules file to append djangofloor extra info
        rules_filename = os.path.join(target_dir, 'debian', 'rules')
        new_rules_content = ''
        python2_re = re.compile(r'^\s*python setup.py install --force --root=debian/([^/\s]+) .*$')
        python3_re = re.compile(r'^\s*python3 setup.py install --force --root=debian/([^/\s]+) .*$')
        debian_names = {}
        # debian_names[2] = 'python-my_project', debian_names[3] = 'python3-my_project'
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

        values = {'project_name': project_name, 'process_manager': process_manager,
                  'frontend': frontend, 'debian_project_name': debian_project_name, }
        # get options for installation/remove scripts
        extra_postinst = {2: self.get_option(project_name, 'extra_postinst', fallback=None),
                          3: self.get_option(project_name, 'extra_postinst3', fallback=None), }
        scripts = {action: {2: self.get_option(project_name, action, fallback=None),
                            3: self.get_option(project_name, '%s3' % action, fallback=None), }
                   for action in ('postinst', 'preinst', 'postrm', 'prerm')}
        # write the default postinst script and custom scripts
        for python_version in (2, 3):
            if python_version not in debian_names:
                continue
            values['extra_postinst'] = ''
            if extra_postinst[python_version]:
                with codecs.open(extra_postinst[python_version], 'r', encoding='utf-8') as fd:
                    values['extra_postinst'] = fd.read()
            values.update({'python_version': python_version, 'debian_name': debian_names[python_version]})
            content = render_to_string('djangofloor/commands/deb_postinst.sh', values)
            python_postinst = os.path.join(target_dir, 'debian', debian_names[python_version] + '.postinst')
            with codecs.open(python_postinst, 'w', encoding='utf-8') as postinst_fd:
                postinst_fd.write(content)
            for action, scripts_per_version in scripts.items():
                if not scripts_per_version[python_version]:
                    continue
                with codecs.open(scripts_per_version[python_version], 'r', encoding='utf-8') as fd:
                    content = fd.read()
                path = os.path.join(target_dir, 'debian', '%s.%s' % (debian_names[python_version], action))
                with codecs.open(path, 'w', encoding='utf-8') as fd:
                    fd.write(content)

        # build the package!
        syscmd = ['dpkg-buildpackage', '-rfakeroot', '-uc', '-b']
        util.process_command(syscmd, cwd=target_dir)
