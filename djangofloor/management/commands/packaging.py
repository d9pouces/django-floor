import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
from argparse import ArgumentParser
from configparser import ConfigParser
from io import StringIO
from subprocess import CalledProcessError

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from djangofloor.management.base import TemplatedBaseCommand
from djangofloor.tasks import get_expected_queues
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


class Process:
    def __init__(self, category, command_line):
        self.category = category
        self.command_line = command_line
        self.binary = shlex.split(command_line)[0]


class CreatedFilesContext:
    """Watch created files in a given directory during some actions.

    """

    def __init__(self, watched_dir):
        self.watched_dir = watched_dir
        self.initial_files = None
        self.new_files = {}
        self.single_created_file = None

    def __enter__(self):
        self.initial_files = self.get_dist_files()
        return self

    def get_dist_files(self):
        if not os.path.isdir(self.watched_dir):
            return {}
        return {x: os.stat(os.path.join(self.watched_dir, x)).st_mtime for x in os.listdir(self.watched_dir)}

    def __exit__(self, exc_type, exc_val, exc_tb):
        new_files = self.get_dist_files()
        for dist_filename, mtime in new_files.items():
            if mtime > self.initial_files.get(dist_filename, 0.0):
                dist_path = os.path.join(self.watched_dir, dist_filename)
                self.new_files[dist_path] = dist_filename
                if self.single_created_file is None:
                    self.single_created_file = (dist_path, dist_filename)
                else:
                    self.single_created_file = None


class Command(TemplatedBaseCommand):
    """Create a complete Debian package using a Vagrant box. You must build a different package for each distrib."""
    default_written_files_locations = [('djangofloor', 'djangofloor/packaging'),
                                       (settings.DF_MODULE_NAME, '%s/packaging' % settings.DF_MODULE_NAME)]
    packaging_config_files = ['dev/config-packaging.ini']
    available_distributions = {'ubuntu/precise64': 'deb', 'ubuntu/trusty64': 'deb', 'ubuntu/wily64': 'deb',
                               'ubuntu/xenial64': 'deb', 'ubuntu/yakkety64': 'deb', 'ubuntu/zesty64': 'deb',
                               'ubuntu/artful64': 'deb',
                               'debian/wheezy64': 'deb', 'debian/jessie64': 'deb', 'debian/stretch64': 'deb',
                               'centos/7': 'rpm', 'fedora/25-cloud-base': 'rpm'
                               }
    BUILD_PACKAGE = 1
    SHOW_CONFIG = 2
    DO_NOT_DESTROY_VAGRANT = 4
    RUN_PACKAGE_AFTER_BUILD = 8
    hooks_section = 'global'
    processes_section = 'processes'

    def __init__(self, stdout=None, stderr=None, no_color=False):
        super(Command, self).__init__(stdout=stdout, stderr=stderr, no_color=no_color)
        self.build_dir = None
        self.dist_dir = None
        self.hooks = {
            'pre_prepare_vagrant_box': None, 'post_prepare_vagrant_box': None,
            'pre_install_project': None, 'post_install_project': None,
            'pre_install_config': None, 'post_install_config': None,
            'pre_install_python': None, 'post_install_python': None,
            'pre_build_package': None, 'post_build_package': None,
            'pre_run_package': None, 'post_run_package': None,
            'pre_install_dependencies': None, 'post_install_dependencies': None,
            'pre_destroy_vagrant_box': None, 'post_destroy_vagrant_box': None,
        }
        self.force_mode = False
        self.custom_config_filename = None
        self.default_setting_merger = None
        self.template_context = {}
        self.verbose_mode = False
        self.source_dir = '.'
        self.vagrant_distrib = 'ubuntu/artful64'
        self.written_files_locations = []
        self.processes = {}

        self.run_options = 0
        self.action = self.BUILD_PACKAGE

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('--build-dir', default='./build')
        parser.add_argument('--dist-dir', default='./dist')
        parser.add_argument('-C', '--config', help='Config file for FPM packaging and default config file',
                            default=None)
        parser.add_argument('--show-config', help='Display a most complete configuration file, displaying '
                                                  'all available options.', action='store_true', default=False)
        parser.add_argument('--source-dir', default='.', help='Path of your project source. '
                                                              '"." by default, expecting that you run this command '
                                                              'from the source dir.')
        parser.add_argument('--clean', help='Remove temporary dirs',
                            action='store_true', default=False)
        parser.add_argument('--distrib', default=self.vagrant_distrib, choices=tuple(self.available_distributions))
        parser.add_argument('--no-destroy', default=False, action='store_true',
                            help='Do not destroy the Vagrant virtual machine')
        parser.add_argument('--run-package', default=False, action='store_true',
                            help='Do not destroy the Vagrant virtual machine, install package and run processes')
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
        self.custom_config_filename = options['config']
        if options['no_destroy']:
            self.run_options |= self.DO_NOT_DESTROY_VAGRANT
        if options['run_package']:
            self.run_options |= self.RUN_PACKAGE_AFTER_BUILD
        if options['show_config']:
            self.run_options |= self.SHOW_CONFIG
        else:
            self.run_options |= self.BUILD_PACKAGE
        parser = self.get_config_parser()
        for hook_name in self.hooks:
            if parser.has_option(self.hooks_section, hook_name):
                self.hooks[hook_name] = parser.get(self.hooks_section, hook_name)
        self.default_setting_merger = self.get_merger([options['config']] if options['config'] else [])
        self.template_context = self.get_template_context(self.default_setting_merger, options['extra_context'])
        for value in options['include']:
            module_name, sep, folder_name = value.partition(':')
            if sep != ':':
                self.stderr.write('Invalid "include" value: %s' % value)
                continue
            self.written_files_locations.append((module_name, folder_name))
        if not self.written_files_locations:
            self.written_files_locations = self.default_written_files_locations

    def handle(self, *args, **options):
        self.load_options(options)
        self.prepare_vagrant_box()
        try:
            self.install_python()
            self.install_project(self.available_distributions[self.vagrant_distrib])
            self.install_dependencies()
            if self.run_options & self.BUILD_PACKAGE:
                self.install_config()
                self.build_package(self.available_distributions[self.vagrant_distrib])
            elif self.run_options & self.SHOW_CONFIG:
                self.show_config(self.available_distributions[self.vagrant_distrib])
            if self.run_options & self.RUN_PACKAGE_AFTER_BUILD:
                self.run_package()
        except CalledProcessError:
            pass
        finally:
            self.destroy_vagrant_box()

    @cached_property
    def host_install_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'opt'), parent=False)

    @cached_property
    def host_tmp_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'tmp'), parent=False)

    @cached_property
    def host_package_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'pkg'), parent=False)

    @cached_property
    def host_fpm_project_config_filename(self):  # written by 'get_project_info.py' from the Vagrant box
        return os.path.join(self.host_tmp_dir, 'fpm-project.ini')

    @cached_property
    def host_fpm_default_config_filename(self):
        return os.path.join(self.host_tmp_dir, 'fpm-default.ini')

    @cached_property
    def host_fpm_custom_config_filename(self):
        return os.path.join(self.host_tmp_dir, 'fpm-custom.ini')

    @cached_property
    def vagrant_box_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'vagrant'), parent=False)

    @cached_property
    def vagrant_install_dir(self):
        return os.path.join('/opt', settings.DF_MODULE_NAME)

    @cached_property
    def vagrant_package_dir(self):
        return '/pkg'

    @cached_property
    def vagrant_fpm_project_config_filename(self):
        return os.path.join(self.vagrant_tmp_dir, 'fpm-project.ini')

    @cached_property
    def vagrant_fpm_custom_config_filename(self):
        return os.path.join(self.vagrant_tmp_dir, 'fpm-custom.ini')

    @cached_property
    def vagrant_fpm_default_config_filename(self):
        return os.path.join(self.vagrant_tmp_dir, 'fpm-default.ini')

    @cached_property
    def vagrant_tmp_dir(self):
        return os.path.join('/tmp', settings.DF_MODULE_NAME)

    @cached_property
    def bind_dirs(self):
        return [(self.host_tmp_dir, self.vagrant_tmp_dir), (self.host_package_dir, self.vagrant_package_dir)]

    def execute_hook(self, hook_name):
        if not self.hooks[hook_name]:
            return False
        self.stdout.write(self.style.NOTICE('executing %s hook [%s]…' % (hook_name, self.hooks[hook_name])))
        func = import_string(self.hooks[hook_name])
        func(self)
        return True

    def prepare_vagrant_box(self):
        self.execute_hook('pre_prepare_vagrant_box')
        # noinspection PyUnresolvedReferences
        vagrant_content = render_to_string('djangofloor/vagrant/Vagrantfile', self.template_context)
        with open(os.path.join(self.vagrant_box_dir, 'Vagrantfile'), 'w') as fd:
            fd.write(vagrant_content)
        subprocess.check_call(['vagrant', 'up'], cwd=self.vagrant_box_dir)
        self.execute_hook('post_prepare_vagrant_box')

    def destroy_vagrant_box(self):
        if self.run_options & (self.DO_NOT_DESTROY_VAGRANT | self.RUN_PACKAGE_AFTER_BUILD):
            return
        self.execute_hook('pre_destroy_vagrant_box')
        subprocess.check_call(['vagrant', 'destroy', '--force'], cwd=self.vagrant_box_dir)
        self.execute_hook('post_destroy_vagrant_box')

    def install_python(self):
        self.stdout.write(self.style.SUCCESS('installing Python…'))
        self.execute_hook('pre_install_python')
        self.copy_vagrant_script('djangofloor/vagrant/install_python.sh')
        self.execute_hook('post_install_python')

    def install_project(self, package_type):
        self.stdout.write(self.style.SUCCESS('creating dist file…'))
        self.execute_hook('pre_install_project')
        with CreatedFilesContext(os.path.join(self.source_dir, 'dist')) as ctx:
            subprocess.check_call(['python3', 'setup.py', 'sdist'], cwd=self.source_dir)
        if ctx.single_created_file is None:
            raise ValueError('unable to create source dist file')
        (dist_path, dist_filename) = ctx.single_created_file
        shutil.copy2(dist_path, os.path.join(self.host_tmp_dir, dist_filename))

        self.stdout.write(self.style.SUCCESS('installing source file…'))
        self.copy_vagrant_script('djangofloor/vagrant/install_project.sh', {'dist_filename': dist_filename})
        self.copy_vagrant_script('djangofloor/vagrant/fpm-default.ini', execute=False,
                                 host_filename=self.host_fpm_default_config_filename,
                                 vagrant_filename=self.vagrant_fpm_default_config_filename)
        self.copy_vagrant_script('djangofloor/vagrant/get_project_info.py')
        self.update_template_context(package_type)
        self.execute_hook('post_install_project')

    def install_dependencies(self):
        self.stdout.write(self.style.SUCCESS('installing extra Python dependencies…'))
        self.execute_hook('pre_install_dependencies')
        self.copy_vagrant_script('djangofloor/vagrant/install_dependencies.sh')
        self.execute_hook('post_install_dependencies')

    def install_config(self):
        self.stdout.write(self.style.SUCCESS('installing static files…'))
        self.execute_hook('pre_install_config')
        writers = self.get_file_writers(self.written_files_locations, context=self.template_context)
        for target_filename in sorted(writers):  # fix the writing order
            writer = writers[target_filename]
            writer.write(self.host_package_dir, self.template_context, dry_mode=False, verbose_mode=self.verbose_mode)
        # noinspection PyUnresolvedReferences
        script_content = render_to_string('djangofloor/vagrant/systemd-web.service', self.template_context)
        # noinspection PyStringFormat
        filename = os.path.join(self.host_package_dir, 'etc', 'systemd', 'system',
                                '%(DF_MODULE_NAME)s-HTTP-worker.service' % self.template_context)
        ensure_dir(filename, parent=True)
        with open(filename, 'w') as fd:
            fd.write(script_content)
        local_template_context = {}
        local_template_context.update(self.template_context)
        for queue in get_expected_queues():
            local_template_context['queue'] = queue
            # noinspection PyUnresolvedReferences
            script_content = render_to_string('djangofloor/vagrant/systemd-worker.service', local_template_context)
            # noinspection PyStringFormat
            filename = os.path.join(self.host_package_dir, 'etc', 'systemd', 'system',
                                    '%(DF_MODULE_NAME)s-%(queue)s.service' % local_template_context)
            with open(filename, 'w') as fd:
                fd.write(script_content)
        self.copy_vagrant_script('djangofloor/vagrant/configure_project.sh')
        self.execute_hook('post_install_config')

    def run_package(self):
        self.execute_hook('pre_run_package')

        self.stdout.write(self.style.SUCCESS('run the created package…'))
        self.copy_vagrant_script('djangofloor/vagrant/run_package.sh')
        self.execute_hook('post_run_package')

    def build_package(self, package_type):
        self.execute_hook('pre_build_package')
        self.stdout.write(self.style.SUCCESS('building %s package…') % package_type)
        cmd = self.get_fpm_command_line(package_type)
        with open(os.path.join(self.host_tmp_dir, 'fpm.json'), 'w') as fd:
            json.dump(cmd, fd)
        with CreatedFilesContext(self.host_tmp_dir) as ctx:
            self.copy_vagrant_script('djangofloor/vagrant/create_package.sh')
        package_src_filename = None
        for key, value in ctx.new_files.items():
            if value.endswith('.%s' % package_type):
                package_src_filename = key
        if package_src_filename:
            package_basename = os.path.basename(package_src_filename)
            package_dst_filename = os.path.join(self.dist_dir, package_basename)
            shutil.copy2(package_src_filename, package_dst_filename)
            self.stdout.write(self.style.SUCCESS('package %s created' % package_dst_filename))
            self.template_context['package_filename'] = package_basename
            self.copy_vagrant_script('djangofloor/vagrant/run_package.sh', execute=False)
        else:
            self.stdout.write(self.style.ERROR('no package has been created'))

        self.execute_hook('post_build_package')

    def show_config(self, package_type):
        current_parser = self.get_config_parser()
        new_parser = ConfigParser()

        new_parser.add_section(self.hooks_section)
        for key in self.hooks:
            if current_parser.has_section(self.hooks_section) and current_parser.has_option(self.hooks_section, key):
                new_parser.set(self.hooks_section, key, current_parser[self.hooks_section][key])
            else:
                new_parser.set(self.hooks_section, key, 'example.module.hook_function')

        new_parser.add_section(self.processes_section)
        for key in current_parser.options(self.processes_section):
            new_parser.set(self.processes_section, key, current_parser[self.processes_section][key])
        for key, fpm_option in sorted(FPM_CLI_OPTIONS.items()):
            section, sep, option_name = key.partition('.')
            if section != package_type:
                continue
            value = '%s fpm option' % fpm_option
            if fpm_option in FPM_TEMPLATED_OPTIONS:
                value += ' [name of a valid Django template]'
            elif fpm_option in FPM_BOOL_OPTIONS:
                value += ' ["true" or "false"]'
            elif fpm_option in FPM_MULTIPLE_OPTIONS:
                value += ' [one value per line\n   (each extra line must starts by two spaces)]'
            if current_parser.has_option(section, option_name):
                value += ' [current value: %s]' % current_parser[section][option_name]
            if not new_parser.has_section(section):
                new_parser.add_section(section)
            new_parser.set(section, option_name, value)
        fp = StringIO()
        new_parser.write(fp)
        self.stdout.write(self.style.SUCCESS(fp.getvalue()))

    def get_template_context(self, merger, extra_context):
        context = super(Command, self).get_template_context(merger, extra_context)
        context['bind_dirs'] = self.bind_dirs
        context['vagrant_distrib'] = self.vagrant_distrib
        context['vagrant_distrib_family'] = self.vagrant_distrib.partition('/')[0]
        context['install_dir'] = (self.host_install_dir, self.vagrant_install_dir)
        context['package_dir'] = (self.host_package_dir, self.vagrant_package_dir)
        context['tmp_dir'] = (self.host_tmp_dir, self.vagrant_tmp_dir)
        context['expected_celery_queues'] = get_expected_queues()
        context['fpm_default_config_filename'] = (self.host_fpm_default_config_filename,
                                                  self.vagrant_fpm_default_config_filename)
        context['fpm_project_config_filename'] = (self.host_fpm_project_config_filename,
                                                  self.vagrant_fpm_project_config_filename)
        context['fpm_custom_config_filename'] = (self.host_fpm_custom_config_filename,
                                                 self.vagrant_fpm_custom_config_filename)
        return context

    def copy_vagrant_script(self, template_name, context=None, execute=True,
                            host_filename=None, vagrant_filename=None):
        if context is None:
            context = {}
        context.update(self.template_context)
        script_content = render_to_string(template_name, context)
        script_name = os.path.basename(template_name)
        if host_filename is None:
            host_filename = os.path.join(self.host_tmp_dir, script_name)
        with open(host_filename, 'w') as fd:
            fd.write(script_content)
        if execute:
            binary = 'bash'
            if script_name.endswith('.py'):
                binary = '%s/bin/python3' % self.vagrant_install_dir
            if vagrant_filename is None:
                vagrant_filename = os.path.join(self.vagrant_tmp_dir, script_name)
            cmd = ['vagrant', 'ssh', '-c', 'sudo %s %s' % (binary, vagrant_filename)]
            try:
                env = {}
                env.update(os.environ)
                env.update({
                    'LC_CTYPE': 'en_US.UTF-8',
                    'LC_MESSAGES': 'en_US.UTF-8',
                    'LC_ALL': 'en_US.UTF-8',
                })
                subprocess.check_call(cmd, cwd=self.vagrant_box_dir, env=env)
            except CalledProcessError as e:
                self.stderr.write('%s returned non-zero exit status.' % ' '.join(cmd))
                raise e

    def get_config_parser(self):
        parser = ConfigParser()
        filenames = [self.host_fpm_default_config_filename, self.host_fpm_project_config_filename,
                     './dev/fpm-config.ini', self.custom_config_filename]
        config_files = [filename for filename in filenames if filename and os.path.isfile(filename)]
        parser.read(config_files)
        return parser

    def get_fpm_command_line(self, package_type):
        parser = self.get_config_parser()
        cmd = ['fpm', '-s', 'dir', '-f', '-t', package_type, '--log', 'error']
        for ini_option, cli_option in FPM_CLI_OPTIONS.items():
            section, sep, option = ini_option.partition('.')
            if section != package_type:
                continue
            if not parser.has_option(section, option):
                section = 'DEFAULT'
            if not parser.has_option(section, option):
                continue
            if cli_option in FPM_BOOL_OPTIONS:
                value = parser.getboolean(section, option)
                if value:
                    cmd += [cli_option]
            elif cli_option in FPM_MULTIPLE_OPTIONS:
                for value in parser.get(section, option).splitlines():
                    cmd += [cli_option, value]
            elif cli_option in FPM_TEMPLATED_OPTIONS:
                template_name = parser.get(section, option)
                content = render_to_string(template_name, self.template_context)
                sha1 = hashlib.sha1(content.encode('utf-8')).hexdigest()
                filename = os.path.join(self.host_tmp_dir, '%s.%s' % (os.path.basename(template_name), sha1))
                with open(filename, mode='w', encoding='utf-8') as fd:
                    fd.write(content)
                filename = os.path.join(self.vagrant_tmp_dir, '%s.%s' % (os.path.basename(template_name), sha1))
                cmd += [cli_option, filename]
            else:
                cmd += [cli_option, parser.get(section, option)]
        cmd += ['%s/=/' % self.vagrant_package_dir]
        return cmd

    def update_template_context(self, package_type):
        parser = self.get_config_parser()
        regex = re.compile(r'(?P<module>[\w.]+)\s*(:\s*(?P<attr>[\w.]+))?\s*(?P<extras>\[.*\])?\s*$', flags=re.UNICODE)
        process_categories = {'django': None, 'gunicorn': None, 'uwsgi': None, 'aiohttp': None, 'celery': None,
                              'control': None}
        for option_name in parser.options('processes'):
            option_matcher = regex.match(parser.get('processes', option_name))
            if not option_matcher:
                continue
            values = option_matcher.groupdict()
            if values['attr'] not in process_categories or values['module'] != 'djangofloor.scripts':
                continue
            elif process_categories[values['attr']]:
                continue
            process_categories[values['attr']] = os.path.join(self.vagrant_install_dir, 'bin', option_name)
        processes = {key: Process(key, value) for (key, value) in process_categories.items() if value}
        self.template_context['processes'] = self.processes or processes
        self.template_context['dependencies'] = []
        if parser.has_option(package_type, 'depends'):
            self.template_context['dependencies'] = [x.strip()
                                                     for x in parser.get(package_type, 'depends').splitlines()
                                                     if x.strip()]
