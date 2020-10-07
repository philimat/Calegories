from distutils import log
from distutils.dep_util import newer
import os
import fnmatch
import re


def tryint(s):
    try:
        return int(s)
    except:
        return s


def natsort_key(s):
    return [tryint(c) for c in re.split(r'(\d+)', s)]


def find_files(top_dir, directory, patterns):
    tdir = os.path.join(top_dir, directory)
    for root, dirs, files in os.walk(tdir):
        for basename in files:
            for pattern in patterns:
                if fnmatch.fnmatch(basename, pattern):
                    filepath = os.path.join(root, basename)
                    filename = os.path.relpath(filepath, top_dir)
                    yield filename


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    top_dir = os.path.abspath(os.path.join(script_dir, '..'))
    resources_dir = os.path.join(top_dir, 'resources')
    qrc_file = os.path.join(script_dir, 'calegories.qrc')
    images = [i for i in find_files(
        resources_dir, 'images', ['*.gif', '*.png'])]
    new_images = 0
    for filename in images:
        filepath = os.path.join(resources_dir, filename)
        if newer(filepath, qrc_file):
            new_images += 1
    if new_images:
        log.info(f'{new_images} images newer than {qrc_file} found')
        with open(qrc_file, 'wb+') as f:
            f.write(b'<!DOCTYPE RCC><RCC version="1.0">\n<qresource>\n')
            for filename in sorted(images, key=natsort_key):
                f.write(('  <file>%s</file>\n' %
                         filename.replace('\\', '/')).encode())
            f.write(b'</qresource>\n<RCC>\n')
            log.info(f'File {qrc_file} written, {len(images)} images')


if __name__ == '__main__':
    log.set_verbosity(1)
    main()
