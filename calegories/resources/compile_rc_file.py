from distutils import log
from distutils.dep_util import newer
import os
import subprocess


def main():
    qrc_file = 'calegories.qrc'
    script_dir = os.path.dirname(os.path.abspath(__file__))
    top_dir = os.path.abspath(os.path.join(script_dir, '..'))
    qrc_path = os.path.join(script_dir, qrc_file)
    py_file = os.path.join(
        top_dir, f'{os.path.splitext(os.path.basename(qrc_path))[0]}_rc.py')
    if os.path.exists(qrc_path):
        if newer(qrc_path, py_file):
            pyrcc = 'pyside2rcc'
            cmd = [pyrcc, qrc_path, '-o', py_file]
            status = subprocess.call(cmd, shell=True)
            if status:
                log.warn(f'Unable to compile resource file {py_file}')
            else:
                log.info(f'File {py_file} written')
    else:
        log.info(f'{qrc_file} was not found')


if __name__ == '__main__':
    log.set_verbosity(1)
    main()
