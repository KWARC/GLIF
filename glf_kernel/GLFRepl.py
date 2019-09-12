import sys
import os
import signal
import time
import re

from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory
from .utils import readFile, parse, parse_command, to_message_format
from .MMTInterface import MMTInterface




class GLFRepl:

    def __init__(self, GF_BIN):
        self.GF_BIN = GF_BIN

        GF_ARGS = [
            GF_BIN,
            '--run'
        ]

        self.td = TemporaryDirectory()
        self.to_clean_up = ['.dot', '.png', '.gfo']
        self.out_file_name = os.path.join(self.td.name, 'shell.out')
        self.out = open(self.out_file_name, 'w+')
        self.shell = Popen(GF_ARGS, stdin=PIPE,
                           stdout=self.out, stderr=self.out)
        self.pid = os.getpid()
        self.out_count = 0

        # initialize the MMT interface
        self.mmtInterface = MMTInterface()

        # register the signal handler for the notify process
        signal.signal(signal.SIGUSR1, self.signal_handler)

    def do_shutdown(self):
        "Terminates the GF shell and the MMT subprocess"
        # terminate gf shell
        self.td.cleanup()
        self.shell.communicate(b'q\n')[0]
        self.shell.stdin.close()
        self.shell.kill()

        # terminate mmt
        self.mmtInterface.do_shutdown()

    def clean_up(self):
        """Removes all files whose extensions are contained in `self.to_clean_up`"""
        removed = []
        files = os.listdir('.')
        for file in files:
            _, file_extension = os.path.splitext(file)
            if file_extension in self.to_clean_up:
                removed.append(file)
                os.remove(file)

        if removed:
            s = map(lambda x: 'Removed: %s' % (x), removed)
            return "\n".join(s)
        else:
            return "No files removed"

    def do_export(self, file_name):
        source_path = os.path.join(self.mmtInterface.content_path, self.mmtInterface.archive, 'source')
        files = os.listdir(source_path)
        file_reg = re.compile('^%s.gf$' % (file_name))
        for file in files:
            if file_reg.match(file):
                from shutil import copy2
                copy2(os.path.join(source_path, file), file)
                return 'Exported %s' % (file)
        return 'Could not find %s' % (file_name)

    def handle_input(self, code):
        """Handles all kinds of user inputs"""
        messages = []
        parse_dict = parse(code)
        if parse_dict['type']:
            if parse_dict['type'] == 'commands':
                for command in parse_dict['commands']:
                    name = command['name']
                    args = command['args']
                    if name == 'view':
                        messages.append(
                            self.handle_multiple_view(' '.join(args)))
                    elif name == 'clean':
                        messages.append(to_message_format(
                            message=self.clean_up()))
                    elif name == 'export':
                        if len(args) > 1:
                            messages.append(to_message_format(
                                message="export only takes one argument!"))
                        else:
                            messages.append(to_message_format(
                                message=self.do_export(args[0])))
                    elif name == 'archive':
                        if len(args) > 2:
                            messages.append(to_message_format(
                                message="archive takes at maximum two arguments!"))
                        else:
                            messages.append(to_message_format(
                                message=self.mmtInterface.handle_archive(args)))
                    elif name == 'request':
                        messages.append(to_message_format(
                            message=self.mmtInterface.handle_request(args)))
                    elif name == 'help':
                        # TODO move this to another external file (probably a json)
                        messages.append(to_message_format("""Available kernel commands: 
view 'gf_command' : view the graph(s) generated by 'gf_command'
clean : remove all %s files from the current directory.
export 'name' : export the grammar with 'name' to your current directory
h : display more information on the GF shell commands
Otherwise you can use the kernel as an editor for your grammars.
Stated grammars are automatically imported upon definiton.""" % (", ".join(self.to_clean_up))))
                    else:
                        cmd = '%s %s' % (name, ' '.join(args))
                        msg = self.handle_shell_input(cmd)
                        if name == 'import' and not msg:
                            messages.append(to_message_format(
                                message='Import successful!'))
                        else:
                            messages.append(to_message_format(message=msg))
            elif parse_dict['type'] == 'GFContent':
                messages.append(to_message_format(
                    message=self.handle_grammar(code, parse_dict['name'])))
            elif parse_dict['type'] == 'MMTContent':
                messages.append(to_message_format(
                    message=self.mmtInterface.create_mmt_file(code, parse_dict['name'], parse_dict['mmt_type'])))

        else:
            messages.append(to_message_format(
                message="Input is neither valid GF or MMT content nor a valid shell command!"))

        return messages

    def handle_grammar(self, content, name):
        """
            Handles a grammar input

            ``grammar``: str; the content of the grammar

            ``name``: str; the name of the grammar
        """
        
        file_path = "%s.gf" % (os.path.join(self.mmtInterface.content_path, self.mmtInterface.archive, 'source', name))
        try:
            with open(file_path, 'w') as f:
                f.write(content)
                f.close()
        except OSError:
            return 'Failed to create grammar %s' % (name)
        out = self.handle_shell_input(
            "import %s" % (file_path))
        if not out:
            self.mmtInterface.build_archive()
            out = "Defined %s" % (name)
        return out

    def handle_multiple_view(self, command):
        """Handles view commands with possibly multiple graph outputs"""
        cmd = parse_command(command)
        if cmd['tree_type']:
            raw_command = cmd['cmd']
            out = self.handle_shell_input(raw_command)
            lines = out.split('\n')
            trees = []
            for line in lines:
                if line != '' and line != ' ':
                    trees.append(line)
            if len(trees) > 1:
                return to_message_format(trees=trees, tree_type=cmd['tree_type'])

        return to_message_format(file=self.handle_single_view(command))

    def handle_single_view(self, command):
        """
            Handles a single view command

            Sends the `command` to the GF shell and converts the output to a .png file
            returns the name of the .png file
        """
        out = self.handle_shell_input(command)
        if not out:
            return "no file"

        out_dot = os.path.join(self.td.name, 'out%s.dot' % (self.out_count))
        out_png = os.path.join(self.td.name, 'out%s.png' % (self.out_count))

        with open(out_dot, 'w') as f:
            f.write(out)

        DOT_ARGS = [
            'dot',
            '-Tpng', out_dot,
            '-o', out_png
        ]
        p = Popen(DOT_ARGS, shell=False)
        p.communicate()[0]
        p.kill()
        self.out_count += 1

        return out_png

    def handle_shell_input(self, code):
        """Sends the `code` to the GF shell"""

        if self.out.closed:
            self.out = open(self.out_file_name, 'w')

        cp_s = self.out.tell()

        # send the command
        code = code+'\n'
        self.shell.stdin.write(code.encode())
        self.shell.stdin.flush()

        # start the notify process
        cmd = 'sp -command=\"python %s/notify.py %s\"\n' % (
            os.path.dirname(os.path.abspath(__file__)), self.pid)
        self.shell.stdin.write(cmd.encode())
        self.shell.stdin.flush()

        # wait for the notify process
        signal.pause()

        # some shell commands (mostly the ones that are dealing with files) are asynchronous from the shells execution,
        # like e.g. searching a file to include. This means the notify process can report back even though the shell
        # hasn't actually written its output to the output file yet. Hence we need to wait a little here to be sure the output is there.
        time.sleep(0.2)
        out = readFile(self.out_file_name, cp_s).replace('ExitFailure 1', '')

        return out

    def start(self):
        """Starts the REPL"""
        i = sys.stdin.readline()
        while i and i != 'quit\n' and i != 'q\n':
            # send input without the newline
            print(self.handle_shell_input(i[:-1]))
            i = sys.stdin.readline()

    def signal_handler(self, signum, frame):
        """Signal handler for the notify process"""
        pass


if __name__ == '__main__':
    repl = GLFRepl('/usr/bin/gf')
    repl.start()
