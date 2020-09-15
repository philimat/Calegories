from distutils import log
from distutils.dep_util import newer
import os
import subprocess
import glob


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    top_dir = os.path.abspath(os.path.join(script_dir, '..'))
    ui_files = glob.glob(f'{script_dir}/ui/*.ui')

    for ui_file in ui_files:
        py_file = os.path.join(
            script_dir, 'ui', f'{os.path.basename(os.path.splitext(ui_file)[0])}_ui.py')
        if not newer(ui_file, py_file):
            continue
        else:
            cmd = ['pyside2-uic', ui_file, '-o', py_file]
            status = subprocess.call(cmd, shell=False)
            if status:
                log.warn(f'Unable to compile resource file {py_file}')
            else:
                log.info(f'File {py_file} written')


if __name__ == '__main__':
    log.set_verbosity(1)
    main()
