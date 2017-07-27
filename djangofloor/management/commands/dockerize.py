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

from django.conf import settings
from django.template.loader import render_to_string
from django.utils.functional import cached_property
from django.utils.module_loading import import_string

from djangofloor.management.base import TemplatedBaseCommand
from djangofloor.tasks import get_expected_queues
from djangofloor.utils import ensure_dir


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
                               'debian/jessie64': 'deb', 'debian/wheezy64': 'deb'}
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
        self.vagrant_distrib = 'ubuntu/xenial64'
        self.written_files_locations = []
        self.processes = {}

        self.run_options = 0
        self.action = self.BUILD_PACKAGE

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        assert isinstance(parser, ArgumentParser)
        parser.add_argument('--build-dir', default='./build/docker')
        parser.add_argument('--dist-dir', default='./dist')
        parser.add_argument('-C', '--config', help='Config file for FPM packaging and default config file',
                            default=None)
        parser.add_argument('--source-dir', default='.', help='Path of your project source. '
                                                              '"." by  default, expecting that you run this command '
                                                              'from the source dir.')
        parser.add_argument('--clean', help='Remove temporary dirs',
                            action='store_true', default=False)
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
        self.custom_config_filename = options['config']
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
        self.package_project()
        self.write_docker_files()
        try:
            pass
            # self.install_project(self.available_distributions[self.vagrant_distrib])
            # self.install_dependencies()
            # if self.run_options & self.BUILD_PACKAGE:
            #     self.install_config()
            #     self.build_package(self.available_distributions[self.vagrant_distrib])
            # elif self.run_options & self.SHOW_CONFIG:
            #     self.show_config(self.available_distributions[self.vagrant_distrib])
            # if self.run_options & self.RUN_PACKAGE_AFTER_BUILD:
            #     self.run_package()
        finally:
            pass
            # self.destroy_vagrant_box()

    @cached_property
    def docker_tmp_dir(self):
        return os.path.join('/tmp', settings.DF_MODULE_NAME)

    @cached_property
    def host_tmp_dir(self):
        return ensure_dir(os.path.join(self.build_dir, 'docker'), parent=False)

    @cached_property
    def host_dockerfile(self):
        return ensure_dir(os.path.join(self.host_tmp_dir, 'Dockerfile'), parent=True)

    @cached_property
    def host_fpm_default_config_filename(self):
        return os.path.join(self.host_tmp_dir, 'fpm-default.ini')

    @cached_property
    def host_fpm_custom_config_filename(self):
        return os.path.join(self.host_tmp_dir, 'fpm-custom.ini')

    def execute_hook(self, hook_name):
        if not self.hooks[hook_name]:
            return False
        self.stdout.write(self.style.NOTICE('executing %s hook [%s]…' % (hook_name, self.hooks[hook_name])))
        func = import_string(self.hooks[hook_name])
        func(self)
        return True

    def write_docker_files(self):
        # self.execute_hook('pre_write_docker_files')
        # noinspection PyUnresolvedReferences
        docker_content = render_to_string('djangofloor/dockerize/Dockerfile', self.template_context)
        with open(self.host_dockerfile, 'w') as fd:
            fd.write(docker_content)
        docker_content = render_to_string('djangofloor/dockerize/install_python.sh', self.template_context)
        with open(os.path.join(self.host_tmp_dir, 'install_python.sh'), 'w') as fd:
            fd.write(docker_content)
        docker_content = render_to_string('djangofloor/dockerize/install_project.sh', self.template_context)
        with open(os.path.join(self.host_tmp_dir, 'install_project.sh'), 'w') as fd:
            fd.write(docker_content)
        docker_content = render_to_string('djangofloor/dockerize/install_dependencies.sh', self.template_context)
        with open(os.path.join(self.host_tmp_dir, 'install_dependencies.sh'), 'w') as fd:
            fd.write(docker_content)
        docker_content = render_to_string('djangofloor/dockerize/configure_project.sh', self.template_context)
        with open(os.path.join(self.host_tmp_dir, 'configure_project.sh'), 'w') as fd:
            fd.write(docker_content)
        docker_content = render_to_string('djangofloor/dockerize/run_project.sh', self.template_context)
        with open(os.path.join(self.host_tmp_dir, 'run_project.sh'), 'w') as fd:
            fd.write(docker_content)
        # self.execute_hook('post_write_docker_files')

    def package_project(self):
        self.stdout.write(self.style.SUCCESS('creating dist file…'))
        # self.execute_hook('pre_install_project')
        with CreatedFilesContext(os.path.join(self.source_dir, 'dist')) as ctx:
            subprocess.check_call(['python3', 'setup.py', 'sdist'], cwd=self.source_dir)
        if ctx.single_created_file is None:
            raise ValueError('unable to create source dist file')
        (dist_path, dist_filename) = ctx.single_created_file
        shutil.copy2(dist_path, os.path.join(self.host_tmp_dir, dist_filename))
        self.stdout.write(self.style.SUCCESS('installing source file…'))
        self.template_context['dist_filename'] = dist_filename
        # self.execute_hook('post_install_project')

    def install_python(self):
        self.stdout.write(self.style.SUCCESS('installing Python…'))
        self.execute_hook('pre_install_python')
        self.copy_vagrant_script('djangofloor/vagrant/install_python.sh')
        self.execute_hook('post_install_python')

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
        fp = StringIO()
        new_parser.write(fp)
        self.stdout.write(self.style.SUCCESS(fp.getvalue()))

    def get_template_context(self, merger, extra_context):
        context = super(Command, self).get_template_context(merger, extra_context)
        context['tmp_dir'] = (self.host_tmp_dir, self.docker_tmp_dir)
        context['expected_celery_queues'] = get_expected_queues()
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
                binary = '%s/bin/python3' % self.docker_install_dir
            if vagrant_filename is None:
                vagrant_filename = os.path.join(self.docker_tmp_dir, script_name)
            cmd = ['vagrant', 'ssh', '-c', 'sudo %s %s' % (binary, vagrant_filename)]
            subprocess.check_call(cmd, cwd=self.vagrant_box_dir)

    def get_config_parser(self):
        parser = ConfigParser()
        filenames = ['./dev/docker-config.ini', self.custom_config_filename]
        config_files = [filename for filename in filenames if filename and os.path.isfile(filename)]
        parser.read(config_files)
        return parser

    def update_template_context(self, package_type):
        parser = self.get_config_parser()
        regex = re.compile(r'(?P<module>[\w.]+)\s*(:\s*(?P<attr>[\w.]+))?\s*(?P<extras>\[.*\])?\s*$', flags=re.UNICODE)
        process_categories = {'django': None, 'gunicorn': None, 'uwsgi': None, 'aiohttp': None, 'celery': None}
        if parser.has_section('processes'):
            for option_name in parser.options('processes'):
                option_matcher = regex.match(parser.get('processes', option_name))
                if not option_matcher:
                    continue
                values = option_matcher.groupdict()
                if values['attr'] not in process_categories or values['module'] != 'djangofloor.scripts':
                    continue
                elif process_categories[values['attr']]:
                    continue
                process_categories[values['attr']] = os.path.join(self.docker_install_dir, 'bin', option_name)
        processes = {key: Process(key, value) for (key, value) in process_categories.items() if value}
        self.template_context['processes'] = self.processes or processes
        self.template_context['dependencies'] = []
        if parser.has_option(package_type, 'depends'):
            self.template_context['dependencies'] = [x.strip()
                                                     for x in parser.get(package_type, 'depends').splitlines()
                                                     if x.strip()]
