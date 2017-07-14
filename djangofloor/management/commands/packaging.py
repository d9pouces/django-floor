# generate Makefile for:
#   installing python deps for compilation
# packaging steps
#   * create virtualenv or compile Python?
#   * installing the project inside this environment
#   * packaging the whole directory
#   * create links to external files:
#       * config /user/local/bin/myproject-* -> /opt/myproject/bin/myproject-*
#       * config /etc/myproject -> /opt/myproject/etc/myproject
#   * config file /opt/myproject/etc/apache2.4
#   * config file /opt/myproject/etc/systemd
#   * config file /opt/myproject/etc/nginx
#   * config file /opt/myproject/etc/supervisor

import codecs
import hashlib
import os
import shlex
import shutil
import subprocess
from argparse import ArgumentParser
from configparser import ConfigParser

import pkg_resources
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from djangofloor.management.base import TemplatedBaseCommand
from djangofloor.utils import ensure_dir
__author__ = 'Matthieu Gallet'
FPM_MULTIPLE_OPTIONS = {'--depends', '--provides', '--conflicts', '--replaces', '--config-files', '--directories',
                        '--deb-build-depends', '--deb-pre-depends', '--rpm-auto-add-exclude-directories'}
FPM_TEMPLATED_OPTIONS = {'--after-install', '--before-install', '--after-remove', '--before-remove', '--after-upgrade',
                         '--before-upgrade', '--deb-custom-control', '--deb-config', '--deb-changelog',
                         '--deb-meta-file', '--rpm-changelog', '--rpm-posttrans', '--rpm-pretrans',
                         '--rpm-verifyscript', '--rpm-trigger-before-install',
                         '--rpm-trigger-after-install', '--rpm-trigger-before-uninstall', '--rpm-trigger-after-targe'}
FPM_BOOL_OPTIONS = {'--rpm-use-file-permissions', '--rpm-sign', '--rpm-auto-add-directories',
                    '--rpm-autoreqprov', '--rpm-autoreq', '--rpm-autoprov',
                    '--rpm-ignore-iteration-in-dependencies', '--rpm-verbatim-gem-dependencies',
                    '--deb-use-file-permissions', '--deb-ignore-iteration-in-dependencies'}
FPM_CLI_OPTIONS = {
    'deb.name': '--name',
    'rpm.name': '--name',
    'tar.name': '--name',
    'deb.version': '--version',
    'rpm.version': '--version',
    'tar.version': '--version',
    'deb.iteration': '--iteration',
    'rpm.iteration': '--iteration',
    'tar.iteration': '--iteration',
    'deb.epoch': '--epoch',
    'rpm.epoch': '--epoch',
    'tar.epoch': '--epoch',
    'deb.license': '--license',
    'rpm.license': '--license',
    'tar.license': '--license',
    'deb.vendor': '--vendor',
    'rpm.vendor': '--vendor',
    'tar.vendor': '--vendor',
    'deb.category': '--category',
    'rpm.category': '--category',
    'tar.category': '--category',
    'deb.depends': '--depends',
    'rpm.depends': '--depends',
    'tar.depends': '--depends',
    'deb.provides': '--provides',
    'rpm.provides': '--provides',
    'tar.provides': '--provides',
    'deb.conflicts': '--conflicts',
    'rpm.conflicts': '--conflicts',
    'tar.conflicts': '--conflicts',
    'deb.replaces': '--replaces',
    'rpm.replaces': '--replaces',
    'tar.replaces': '--replaces',
    'deb.config-files': '--config-files',
    'rpm.config-files': '--config-files',
    'tar.config-files': '--config-files',
    'deb.directories': '--directories',
    'rpm.directories': '--directories',
    'tar.directories': '--directories',
    'deb.architecture': '--architecture',
    'rpm.architecture': '--architecture',
    'tar.architecture': '--architecture',
    'deb.maintainer': '--maintainer',
    'rpm.maintainer': '--maintainer',
    'tar.maintainer': '--maintainer',
    'deb.description': '--description',
    'rpm.description': '--description',
    'tar.description': '--description',
    'deb.url': '--url',
    'rpm.url': '--url',
    'tar.url': '--url',
    'deb.after-install': '--after-install',
    'rpm.after-install': '--after-install',
    'tar.after-install': '--after-install',
    'deb.before-install': '--before-install',
    'rpm.before-install': '--before-install',
    'tar.before-install': '--before-install',
    'deb.after-remove': '--after-remove',
    'rpm.after-remove': '--after-remove',
    'tar.after-remove': '--after-remove',
    'deb.before-remove': '--before-remove',
    'rpm.before-remove': '--before-remove',
    'tar.before-remove': '--before-remove',
    'deb.after-upgrade': '--after-upgrade',
    'rpm.after-upgrade': '--after-upgrade',
    'tar.after-upgrade': '--after-upgrade',
    'deb.before-upgrade': '--before-upgrade',
    'rpm.before-upgrade': '--before-upgrade',
    'tar.before-upgrade': '--before-upgrade',
    'deb.ignore-iteration-in-dependencies': '--deb-ignore-iteration-in-dependencies',
    'deb.build-depends': '--deb-build-depends',
    'deb.pre-depends': '--deb-pre-depends',
    'deb.compression': '--deb-compression',
    'deb.custom-control': '--deb-custom-control',
    'deb.config': '--deb-config',
    'deb.templates': '--deb-templates',
    'deb.installed-size': '--deb-installed-size',
    'deb.priority': '--deb-priority',
    'deb.use-file-permissions': '--deb-use-file-permissions',
    'deb.user': '--deb-user',
    'deb.group': '--deb-group',
    'deb.changelog': '--deb-changelog',
    'deb.recommends': '--deb-recommends',
    'deb.suggests': '--deb-suggests',
    'deb.meta-file': '--deb-meta-file',
    'deb.interest': '--deb-interest',
    'deb.activate': '--deb-activate',
    'deb.field': '--deb-field',
    'deb.shlibs': '--deb-shlibs',
    'deb.init': '--deb-init',
    'deb.default': '--deb-default',
    'deb.upstart': '--deb-upstart',
    'rpm.use-file-permissions': '--rpm-use-file-permissions',
    'rpm.sign': '--rpm-sign',
    'rpm.auto-add-directories': '--rpm-auto-add-directories',
    'rpm.autoreqprov': '--rpm-autoreqprov',
    'rpm.autoreq': '--rpm-autoreq',
    'rpm.autoprov': '--rpm-autoprov',
    'rpm.ignore-iteration-in-dependencies': '--rpm-ignore-iteration-in-dependencies',
    'rpm.verbatim-gem-dependencies': '--rpm-verbatim-gem-dependencies',
    'rpm.user': '--rpm-user',
    'rpm.group': '--rpm-group',
    'rpm.defattrfile': '--rpm-defattrfile',
    'rpm.defattrdir': '--rpm-defattrdir',
    'rpm.rpmbuild-define': '--rpm-rpmbuild-define',
    'rpm.digest': '--rpm-digest',
    'rpm.compression': '--rpm-compression',
    'rpm.os': '--rpm-os',
    'rpm.changelog': '--rpm-changelog',
    'rpm.auto-add-exclude-directories': '--rpm-auto-add-exclude-directories',
    'rpm.attr': '--rpm-attr',
    'rpm.init': '--rpm-init',
    'rpm.filter-from-provides': '--rpm-filter-from-provides',
    'rpm.filter-from-requires': '--rpm-filter-from-requires',
    'rpm.verifyscript': '--rpm-verifyscript',
    'rpm.pretrans': '--rpm-pretrans',
    'rpm.posttrans': '--rpm-posttrans',
    'rpm.trigger-before-install': '--rpm-trigger-before-install',
    'rpm.trigger-after-install': '--rpm-trigger-after-install',
    'rpm.trigger-before-uninstall': '--rpm-trigger-before-uninstall',
    'rpm.trigger-after-target-uninstall': '--rpm-trigger-after-target-uninstall',
}


class Process(object):
    def __init__(self, category, command_line):
        self.category = category
        self.command_line = command_line
        self.binary = shlex.split(command_line)[0]


class Command(TemplatedBaseCommand):
    """Create a Makefile """
    default_searched_locations = [('djangofloor', 'djangofloor/packaging'),
                                  (settings.DF_MODULE_NAME, '%s/packaging' % settings.DF_MODULE_NAME)]
    default_config_files = ['dev/config-packaging.ini']

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout=stdout, stderr=stderr, no_color=no_color)
        self.build_dir = None
        self.dist_dir = None
        self.hooks = {'pre_install_project': None, 'post_install_project': None,
                      'pre_install_config': None, 'post_install_config': None,
                      'pre_install_python': None, 'post_install_python': None,
                      'pre_build_package': None, 'post_build_package': None}
        self.force_mode = False
        self.config_filename = None
        self.default_setting_merger = None
        self.default_template_context = {}
        self.verbose_mode = False
        self.source_dir = '.'
        self.vagrant_distrib = None

        # self.controller = None
        # self.proxy = None
        # self.packages = None
        self.default_config_locations = []
        # self.processes = {}

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('--build-dir', default='./build')
        parser.add_argument('--dist-dir', default='./dist')
        parser.add_argument('-C', '--config', help='Config file for FPM packaging and default config file',
                            default=None)
        parser.add_argument('--source-dir', default='.', help='Path of your project source.'
                                                              '"." by default, expecting that you run this command '
                                                              'from the source dir.')
        parser.add_argument('--clean', help='Remove temporary dirs',
                            action='store_true', default=False)
        parser.add_argument('--distrib', default='ubuntu/trusty64')
        # parser.add_argument('--add-pyton-dep', default=False, action='store_true',
        #                     help='Use the native Python package')
        # parser.add_argument('--package', default=[], action='append',
        #                     choices=['deb', 'rpm', 'tar'])
        parser.add_argument('--include', default=[], action='append',
                            help='Where to search templates and static files.\n'
                                 ' If not used, use "--include djangofloor:djangofloor/packages '
                                 '--include %s:%s/packages".\n\n'
                                 'Syntax: "dotted.module.path:root/folder". '
                                 '\nCan be used multiple times, root/folder must be a subfolder of the "templates" '
                                 'folder.' % (settings.DF_MODULE_NAME, settings.DF_MODULE_NAME))
        parser.add_argument('--extra-context', nargs='*', help='Extra variable for the template system '
                                                               '(--extra-context=NAME:VALUE)', default=[])
        parser.description = """Create a self-contained package (deb, tar or rpm) for the project.
        
        The package is created in a Vagrant box. 
        """

    def load_options(self, options):
        self.build_dir = os.path.abspath(options['build_dir'])
        self.dist_dir = os.path.abspath(options['dist_dir'])
        self.source_dir = options['source_dir']  # project source
        self.verbose_mode = options['verbosity'] > 1
        self.force_mode = options['clean']
        self.vagrant_distrib = options['distrib']

        parser = ConfigParser()
        self.config_filename = options['config']
        if self.config_filename:
            parser.read([self.config_filename])
        for hook_name in list(self.hooks.keys()):
            if parser.has_option('global', hook_name):
                self.hooks[hook_name] = parser.get('global', hook_name)
        self.default_setting_merger = self.get_merger([options['config']] if options['config'] else [])
        self.default_template_context = self.get_template_context(self.default_setting_merger, options['extra_context'])
        # self.controller = parser.get('global', 'controller', fallback='systemd')
        # self.proxy = parser.get('global', 'reverse_proxy', fallback='apache2.4')
        # if parser.has_section('processes'):
        #     for option in parser.options('processes'):
        #         self.processes[option] = Process(option, parser.get('processes', option))
        #
        # self.packages = options['package']
        for value in options['include']:
            module_name, sep, folder_name = value.partition(':')
            if sep != ':':
                self.stderr.write('Invalid "include" value: %s' % value)
                continue
            self.default_config_locations.append((module_name, folder_name))
        if not self.default_config_locations:
            self.default_config_locations = self.default_searched_locations

    def handle(self, *args, **options):
        self.load_options(options)
        self.prepare_vagrant_box(force=self.force_mode)
        try:
            self.install_python(force=self.force_mode)
            self.install_project()
            self.install_config()
        finally:
            self.destroy_vagrant_box(force=self.force_mode)
        # for package in self.packages:
        #     self.build_package(package)

    @cached_property
    def host_python_path(self):
        return os.path.join(self.host_install_dir, 'bin', 'python3')

    @cached_property
    def host_install_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'opt', settings.DF_MODULE_NAME), parent=False)

    @cached_property
    def host_config_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'etc', settings.DF_MODULE_NAME), parent=False)

    @cached_property
    def host_data_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'var', settings.DF_MODULE_NAME), parent=False)

    @cached_property
    def host_log_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'var/log', settings.DF_MODULE_NAME), parent=False)

    @cached_property
    def host_tmp_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'tmp', settings.DF_MODULE_NAME), parent=False)

    @cached_property
    def vagrant_box_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'vagrant'), parent=False)

    @cached_property
    def vagrant_config_dir(self):
        return os.path.join('/etc', settings.DF_MODULE_NAME)

    @cached_property
    def vagrant_data_dir(self):
        return os.path.join('/var', settings.DF_MODULE_NAME)

    @cached_property
    def vagrant_install_dir(self):
        return os.path.join('/opt', settings.DF_MODULE_NAME)

    @cached_property
    def vagrant_log_dir(self):
        return os.path.join('/var/log', settings.DF_MODULE_NAME)

    @cached_property
    def vagrant_tmp_dir(self):
        return os.path.join('/tmp', settings.DF_MODULE_NAME)

    @cached_property
    def bind_dirs(self):
        return [(self.host_tmp_dir, self.vagrant_tmp_dir), (self.host_config_dir, self.vagrant_config_dir),
                (self.host_data_dir, self.vagrant_data_dir), (self.host_log_dir, self.vagrant_log_dir)]

    @cached_property
    def python_package_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'pkg'), parent=False)

    def execute_hook(self, hook_name):
        if not self.hooks[hook_name]:
            return False
        self.stdout.write(self.style.NOTICE('executing %s hook [%s]…' % (hook_name, self.hooks[hook_name])))
        func = import_string(self.hooks[hook_name])
        func(self)
        return True

    def prepare_vagrant_box(self, force=False):
        vagrant_content = render_to_string('djangofloor/vagrant/Vagrantfile', self.default_template_context)
        with open(os.path.join(self.vagrant_box_dir, 'Vagrantfile'), 'w') as fd:
            fd.write(vagrant_content)
        subprocess.check_call(['vagrant', 'up'], cwd=self.vagrant_box_dir)

    def destroy_vagrant_box(self, force=False):
        pass
        # subprocess.check_call(['vagrant', 'destroy', '--force'], cwd=self.vagrant_box_dir)

    def get_template_context(self, merger, extra_context):
        context = super(Command, self).get_template_context(merger, extra_context)
        context['bind_dirs'] = self.bind_dirs
        context['build_dir'] = self.build_dir
        context['vagrant_distrib'] = self.vagrant_distrib
        context['install_dir'] = (self.host_install_dir, self.vagrant_install_dir)
        context['tmp_dir'] = (self.host_tmp_dir, self.vagrant_tmp_dir)
        context['config_dir'] = (self.host_config_dir, self.vagrant_config_dir)
        context['data_dir'] = (self.host_data_dir, self.vagrant_data_dir)
        context['log_dir'] = (self.host_log_dir, self.vagrant_log_dir)
        # process_categories = {'django': None, 'gunicorn': None, 'uwsgi': None, 'aiohttp': None, 'celery': None}
        #
        # # analyze scripts to detect which processes to launch on startup
        # for script_name, entry_point in pkg_resources.get_entry_map('moneta').get('console_scripts').items():
        #     if entry_point.module_name != 'djangofloor.scripts' or not entry_point.attrs:
        #         continue
        #     daemon_type = entry_point.attrs[0]
        #     if process_categories.get(daemon_type):
        #         continue
        #     process_categories[daemon_type] = os.path.join(self.python_prefix, 'bin', entry_point.name)
        # processes = {key: Process(key, value) for (key, value) in process_categories.items() if value}
        # context['processes'] = self.processes or processes
        return context

    def install_python(self, force=False):
        self.stdout.write(self.style.SUCCESS('installing Python…'))
        self.execute_hook('pre_install_python')
        if os.path.isfile(self.host_python_path) and not force:
            return

        script_content = render_to_string('djangofloor/vagrant/install_python.sh', self.default_template_context)
        script_name = 'install_python.sh'
        with open(os.path.join(self.host_tmp_dir, script_name), 'w') as fd:
            fd.write(script_content)
        cmd = ['vagrant', 'ssh', '-c', 'sudo bash %s' % os.path.join(self.vagrant_tmp_dir, script_name)]
        subprocess.check_call(cmd, cwd=self.vagrant_box_dir)
        # shutil.rmtree(src_dir)
        self.execute_hook('post_install_python')

    def install_project(self):
        self.stdout.write(self.style.SUCCESS('creating dist file…'))
        self.execute_hook('pre_install_project')
        dist_dir = os.path.join(self.source_dir, 'dist')

        def get_dist_files():
            if not os.path.isdir(dist_dir):
                return {}
            return {x: os.stat(os.path.join(dist_dir, x)).st_mtime for x in os.listdir(dist_dir)}

        current_files = get_dist_files()
        subprocess.check_call(['python3', 'setup.py', 'sdist'], cwd=self.source_dir)
        new_files = get_dist_files()
        dist_path, dist_filename = None, None
        for dist_filename, mtime in new_files.items():
            if mtime > current_files.get(dist_filename, 0.0):
                dist_path = os.path.join(dist_dir, dist_filename)
        if not dist_path:
            raise ValueError('unable to create source dist file')
        shutil.copy2(dist_path, os.path.join(self.host_tmp_dir, dist_filename))

        self.stdout.write(self.style.SUCCESS('installing source file…'))
        context = {'dist_filename': dist_filename}
        context.update(self.default_template_context)
        script_content = render_to_string('djangofloor/vagrant/install_project.sh', context)
        script_name = 'install_source.sh'
        with open(os.path.join(self.host_tmp_dir, script_name), 'w') as fd:
            fd.write(script_content)
        cmd = ['vagrant', 'ssh', '-c', 'sudo bash %s' % os.path.join(self.vagrant_tmp_dir, script_name)]
        subprocess.check_call(cmd, cwd=self.vagrant_box_dir)

        self.execute_hook('post_install_project')

    def install_config(self):
        self.stdout.write(self.style.SUCCESS('installing config…'))
        self.execute_hook('pre_install_config')
        template_context = self.default_template_context
        writers = self.get_file_writers(self.default_config_locations, context=template_context)
        for target_filename in sorted(writers):  # fix the writing order
            writer = writers[target_filename]
            writer.write(self.python_package_dir, template_context, dry_mode=False, verbose_mode=self.verbose_mode)
        self.execute_hook('post_install_config')

    def build_package(self, package):
        self.execute_hook('pre_build_package')
        if os.path.isdir(self.host_tmp_dir):
            shutil.rmtree(self.host_tmp_dir)
        ensure_dir(self.host_tmp_dir, parent=False)
        default_config = self.write_default_fpm_options()
        parser = ConfigParser()
        if self.config_filename:
            parser.read([default_config, self.config_filename])
        else:
            parser.read([default_config])
        # get fpm options
        fpm_options = []
        for ini_option, cli_option in FPM_CLI_OPTIONS.items():
            section, sep, option = ini_option.partition('.')
            if section != package:
                continue
            if not parser.has_option(section, option):
                section = 'DEFAULT'
            if not parser.has_option(section, option):
                continue
            if cli_option in FPM_BOOL_OPTIONS:
                value = parser.getboolean(section, option)
                if value:
                    fpm_options += [cli_option]
            elif cli_option in FPM_MULTIPLE_OPTIONS:
                for value in parser.get(section, option).splitlines():
                    fpm_options += [cli_option, value]
            elif cli_option in FPM_TEMPLATED_OPTIONS:
                template_name = parser.get(section, option)
                content = render_to_string(template_name, self.default_template_context)
                sha1 = hashlib.sha1(content.encode('utf-8')).hexdigest()
                filename = os.path.join(self.host_tmp_dir, '%s.%s' % (os.path.basename(template_name), sha1))
                with codecs.open(filename, mode='w', encoding='utf-8') as fd:
                    fd.write(content)
                fpm_options += [cli_option, filename]
            else:
                fpm_options += [cli_option, parser.get(section, option)]

        self.stdout.write(self.style.SUCCESS('building %s package…') % package)
        cmd = ['fpm', '-s', 'dir', '-f', '-t', package, '--log', 'error'] + fpm_options + \
              ['%s/=%s' % (self.python_package_dir, '/')]
        subprocess.check_call(cmd, cwd=self.python_package_dir)
        self.execute_hook('post_build_package')

    def write_default_fpm_options(self):
        default_config = os.path.join(self.host_tmp_dir, 'config.ini')
        parser = ConfigParser()
        defaults = {'version': settings.DF_PROJECT_VERSION, 'name': settings.DF_MODULE_NAME}
        maintainer = [None, None]
        # noinspection PyBroadException
        try:
            for line in pkg_resources.get_distribution(settings.DF_MODULE_NAME).get_metadata_lines('PKG-INFO'):
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
        with codecs.open(default_config, 'w', encoding='utf-8') as fd:
            parser.write(fd)
        return default_config
