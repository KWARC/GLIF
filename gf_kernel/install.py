import argparse
import json
import os
import sys

from jupyter_client.kernelspec import KernelSpecManager
from IPython.utils.tempdir import TemporaryDirectory


kernel_json = {
    "argv": [sys.executable, "-m", "gf_kernel", "-f", "{connection_file}"],
    "display_name": "GF",
    "language": "gf",
}


def install_my_kernel_spec(user=True, prefix=None):
    with TemporaryDirectory() as td:
        os.chmod(td, 0o755)  # Starts off as 700, not user readable
        with open(os.path.join(td, 'kernel.json'), 'w') as f:
            json.dump(kernel_json, f, sort_keys=True)

        # copy kernel.js to the right place
        import shutil
        dir_path = os.path.dirname(os.path.realpath(__file__))
        jsPath = os.path.join(dir_path, os.path.join('js', 'kernel.js'))
        shutil.copy2(jsPath, td)

        # copy gf.css to the right place
        css = os.path.join(dir_path, os.path.join('css', 'gf.css'))
        shutil.copy2(css, td)

        print('Installing Jupyter kernel spec GF')
        KernelSpecManager().install_kernel_spec(td, 'GF', user=user, prefix=prefix)


def _is_root():
    try:
        return os.geteuid() == 0
    except AttributeError:
        return False  # assume not an admin on non-Unix platforms


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('--user', action='store_true',
                    help="Install to the per-user kernels registry. Default if not root.")
    ap.add_argument('--sys-prefix', action='store_true',
                    help="Install to sys.prefix (e.g. a virtualenv or conda env)")
    ap.add_argument('--prefix',
                    help="Install to the given prefix. "
                    "Kernelspec will be installed in {PREFIX}/share/jupyter/kernels/")
    args = ap.parse_args(argv)

    if args.sys_prefix:
        args.prefix = sys.prefix
    if not args.prefix and not _is_root():
        args.user = True

    install_my_kernel_spec(user=args.user, prefix=args.prefix)


if __name__ == '__main__':
    main()
