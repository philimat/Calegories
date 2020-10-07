#!/usr/bin/env python

import fnmatch
import glob
import shutil
import subprocess
import os
import re
import sys
from distutils import log
import distutils.command.build as distutils_build
import distutils.command.clean as distutils_clean
import setuptools

DISPLAY_NAME = 'Calegories'
ICON = 'calegories.ico'
NAME = 'calegories'
AUTHOR = 'Matt Philippi'
DESCRIPTION = 'A time sheet generator derived from categorized calendar entries'
URL = 'https://github.com/philimat/Calegories.git'
BASE_DIR = os.path.dirname(os.path.realpath(__file__))
SRC_DIR = os.path.join(BASE_DIR, NAME)

sys.path.insert(0, SRC_DIR)

with open(f'{NAME}/version.py', 'r') as fd:
    VERSION = re.search(
        r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', fd.read(), re.MULTILINE).group(1)

with open('requirements.txt', 'r') as f:
    REQUIRES = f.read().splitlines()

with open('requirements-dev.txt', 'r') as f:
    REQUIRES_DEV = f.read().splitlines()


class BuildQt(setuptools.Command):

    description = "Build the Qt interface"

    boolean_options = []
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        sys.path.insert(0, os.path.join(BASE_DIR, SRC_DIR, "resources"))
        from resources import compile_rc_file, compile_ui_files, make_qrc_file
        make_qrc_file.main()
        compile_rc_file.main()
        compile_ui_files.main()


class CleanLocal(setuptools.Command):

    description = "Clean the local project directory"

    wildcards = ['*.py[co]', '*_ui.py', '*_rc.py', '__pycache__']
    excludedirs = ['.git', 'build', 'dist']
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

        def _walkpaths(self, path):
            for root, dirs, files in os.walk(path):
                for excluded_dir in self.excludedirs:
                    abs_excluded_dir = os.path.join(path, excluded_dir)
                    if root == abs_excluded_dir or root.startswith(abs_excluded_dir + os.sep):
                        continue

    def run(self):
        for a_path in self._walkpaths('.'):
            if os.path.isdir(a_path):
                shutil.rmtree(a_path)
            else:
                os.remove(a_path)


class BuildExe(setuptools.Command):
    """
    Python requirements in requirements-build.txt
    """

    description = "Generates a .exe file for distribution"

    boolean_options = []
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run_build_exe(self):
        spec_file = f'{NAME}.spec'
        subprocess.call(['pyinstaller', spec_file, '--noconfirm'])

    def run(self):
        self.run_command('build_qt')
        self.run_build_exe()


class BuildInstaller(setuptools.Command):
    """
    Requires NSIS found at https://nsis.sourceforge.io/Download"
    """

    description = "Generates a .exe file for installation on Windows"

    boolean_options = []
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run_build_installer(self):
        installer_dir = os.path.join(BASE_DIR, 'installer')

        build_number = 0
        file_version = f'{VERSION}.{build_number}'

        installer_args = {
            'display_name': DISPLAY_NAME,
            'description': DESCRIPTION,
            'version': VERSION,
            'file_version': file_version,
            'icon': ICON,
            'base_dir': BASE_DIR,
            'installer_dir': installer_dir,
        }

        nsi_in = os.path.join(installer_dir, '{NAME}.nsi.in')
        nsi_out = os.path.join(installer_dir, '{NAME}.nsi')

        generate_file(nsi_in, nsi_out, installer_args)

        nsis = os.path.join(
            os.environ["ProgramFiles(x86)"], "NSIS", "makensis.exe")
        subprocess.call([nsis, nsi_out])

    def run(self):
        self.run_command("build_exe")
        self.run_build_installer()


class MyBuild(distutils_build.build):
    def run(self):
        self.run_command("build_qt")
        distutils_build.build.run(self)


class MyClean(distutils_clean.clean):
    def run(self):
        self.run_command("clean_local")
        distutils_clean.clean.run(self)


def generate_file(filename_in, filename_out, variables):
    log.info('Generating %s from %s', filename_in, filename_out)
    with open(filename_in, "rt") as f_in:
        with open(filename_out, "wt") as f_out:
            f_out.write(f_in.read() % variables)


setuptools.setup(
    name=NAME,
    version=VERSION,
    author=AUTHOR,
    description=DESCRIPTION,
    url=URL,
    package_dir={DISPLAY_NAME: NAME},
    packages=[NAME],
    install_requires=REQUIRES,
    platforms=["Windows"],
    cmdclass={
        'build': MyBuild,
        'build_qt': BuildQt,
        'build_exe': BuildExe,
        'build_installer': BuildInstaller,
        'clean': MyClean,
        'clean_local': CleanLocal,
    }
)
