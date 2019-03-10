import os

from .utils import to_display_data, get_current_word, get_matches
from .GFRepl import GFRepl

from urllib.parse import quote

from IPython.display import display
from ipywidgets import widgets

from traitlets import Instance, Type, Any, Bool
from ipykernel.kernelbase import Kernel
from ipykernel.comm import CommManager
from ipykernel.zmqshell import ZMQInteractiveShell
from distutils.spawn import find_executable

GF_BIN = find_executable('gf')

# ----------------------------------  KERNEL  ----------------------------------


class GFKernel(Kernel):
    implementation = 'GF'
    implementation_version = '1.0'
    language = 'gf'
    language_version = '0.1'
    # TODO change this to gf
    language_info = {
        'name': 'gf',
        'mimetype': 'text/gf',
        'file_extension': '.gf',
    }
    banner = "GF"

    shell = Instance(
        'IPython.core.interactiveshell.InteractiveShellABC', allow_none=True)
    shell_class = Type(ZMQInteractiveShell)

    use_experimental_completions = Bool(True,
                                        help="Set this flag to False to deactivate the use of experimental IPython completion APIs.",
                                        ).tag(config=True)

    user_module = Any()

    def _user_module_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_module = new

    user_ns = Instance(dict, args=None, allow_none=True)

    def _user_ns_changed(self, name, old, new):
        if self.shell is not None:
            self.shell.user_ns = new
            self.shell.init_user_ns()

    def __init__(self, **kwargs):
        super(GFKernel, self).__init__(**kwargs)
        # set up the shell
        self.shell = self.shell_class.instance(parent=self,
                                               profile_dir=self.profile_dir,
                                               user_module=self.user_module,
                                               user_ns=self.user_ns,
                                               kernel=self,
                                               )
        self.shell.displayhook.session = self.session
        self.shell.displayhook.pub_socket = self.iopub_socket
        self.shell.displayhook.topic = self._topic('execute_result')
        self.shell.display_pub.session = self.session
        self.shell.display_pub.pub_socket = self.iopub_socket

        # set up and attach comm_manager to the shell
        self.comm_manager = CommManager(parent=self, kernel=self)
        self.shell.configurables.append(self.comm_manager)
        comm_msg_types = ['comm_open', 'comm_msg', 'comm_close']
        for msg_type in comm_msg_types:
            self.shell_handlers[msg_type] = getattr(
                self.comm_manager, msg_type)

        # initialize the GFRepl
        self.GFRepl = GFRepl(GF_BIN)

    def start(self):
        self.shell.exit_now = False
        super(GFKernel, self).start()

    def set_parent(self, ident, parent):
        """Overridden from parent to tell the display hook and output streams
        about the parent message.
        """
        super(GFKernel, self).set_parent(ident, parent)
        self.shell.set_parent(parent)

    def init_metadata(self, parent):
        """Initialize metadata.
        Run at the beginning of each execution request.
        """
        md = super(GFKernel, self).init_metadata(parent)
        # FIXME: remove deprecated ipyparallel-specific code
        # This is required for ipyparallel < 5.0
        md.update({
            'dependencies_met': True,
            'engine': self.ident,
        })
        return md

    def do_execute(self, code, silent=False, store_history=True, user_expressions=None, allow_stdin=True):
        """Called when the user inputs code"""
        # img_data = Image.open('/home/kai/gf_content/out.png','r')
        messages = self.GFRepl.handle_input(code)
        for msg in messages:
            if msg['file']:
                file_name = msg['file']
                try:
                    with open(file_name, "rb") as f:
                        img = f.read()
                    display(widgets.Image(value=img, format='png'))
                except:
                    self.send_response(self.iopub_socket, 'display_data', to_display_data(
                        "There is no tree to show!"))

            elif msg['message']:
                self.send_response(
                    self.iopub_socket, 'display_data', to_display_data(msg['message']))

            elif msg['trees']:
                dd = widgets.Dropdown(
                    options=msg['trees'],
                    value=msg['trees'][0],
                    description='Tree of:',
                    disabled=False,
                )
                file_name = self.GFRepl.handle_single_view(
                    "%s %s" % (msg['tree_type'], msg['trees'][0]))
                with open(file_name, "rb") as f:
                    img = f.read()
                image = widgets.Image(value=img, format='png')

                def on_value_change(change):
                    file_name = self.GFRepl.handle_single_view(
                        "%s %s" % (msg['tree_type'], change['new']))
                    with open(file_name, "rb") as f:
                        img = f.read()
                    image.value = img

                dd.observe(on_value_change, names='value')
                display(dd, image)

        return {'status': 'ok',
                # The base class increments the execution count
                'payload': [],
                'execution_count': self.execution_count,
                'user_expressions': {},
                }

    def do_shutdown(self, restart):
        """Called when the kernel is terminated"""
        self.GFRepl.do_shutdown()

    def do_complete(self, code, cursorPos):
        """Autocompletion when the user presses tab"""
        # load the shortcuts from the unicode-latex-map
        last_word = get_current_word(code, cursorPos)
        matches = get_matches(last_word)
        if not last_word or not matches:
            matches = None

        return {
            'matches': matches,
            'cursor_start': cursorPos-len(last_word),
            'cursor_end': cursorPos,
            'metadata': {},
            'status': 'ok'
        }


if __name__ == '__main__':
    from ipykernel.kernelapp import IPKernelApp
    IPKernelApp.launch_instance(kernel_class=GFKernel)
