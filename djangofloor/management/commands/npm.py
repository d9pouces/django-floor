import glob
import os
import shutil
import subprocess

from django.conf import settings
from django.core.management import BaseCommand

from djangofloor.utils import ensure_dir

__author__ = 'Matthieu Gallet'


class Command(BaseCommand):
    help = 'Use npm to download all packages that are keys of "settings.NPM_FILE_PATTERNS"'

    # def add_arguments(self, parser):
    #     assert isinstance(parser, ArgumentParser)
    #     parser.add_argument('--favicon', default=None,
    #                         help=('path or URL of to master favicon. '
    #                               'Otherwise use "icons/favicon.ico" from the static files'))

    def handle(self, *args, **options):
        verbosity = options['verbosity']
        ensure_dir(settings.NPM_ROOT_PATH, False)
        for npm_package, patterns in settings.NPM_FILE_PATTERNS.items():
            if verbosity > 0:
                self.stdout.write(self.style.SUCCESS('downloading %s') % npm_package)
            command = [settings.NPM_EXECUTABLE_PATH, 'install', npm_package]
            try:
                subprocess.check_output(command, cwd=settings.NPM_ROOT_PATH)
            except OSError:
                print("Unable to execute command %s" % " ".join(command))
                continue
            src_package_root = os.path.join(settings.NPM_ROOT_PATH, 'node_modules', npm_package)
            dst_package_root = os.path.join(settings.STATIC_ROOT, settings.NPM_STATIC_FILES_PREFIX, npm_package)
            ensure_dir(dst_package_root)
            for pattern in patterns:
                if verbosity > 0:
                    self.stdout.write(self.style.SUCCESS('copying %s files' % pattern))
                for src_path in glob.glob(os.path.join(src_package_root, pattern)):
                    dst_path = os.path.join(dst_package_root, os.path.relpath(src_path, src_package_root))
                    ensure_dir(dst_path, parent=True)
                    if verbosity > 1:
                        self.stdout.write(self.style.NOTICE('copying %s to %s') % (src_path, dst_path))
                    if os.path.isfile(dst_path):
                        os.remove(dst_path)
                    elif os.path.isdir(dst_path):
                        shutil.rmtree(dst_path)
                    if os.path.isfile(src_path):
                        shutil.copy(src_path, dst_path)
                    else:
                        shutil.copytree(src_path, dst_path)
