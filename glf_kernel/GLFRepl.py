import sys
import os
import signal
import time
import re

from json import load
from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory
from .utils import parse, to_message_format, get_name, get_args, GF_commands, tree
from .MMTInterface import MMTInterface
from .GFRepl import GFRepl
from distutils.spawn import find_executable


class GLFRepl:

    def __init__(self):
        # initialize the MMT interface
        self.mmtInterface = MMTInterface()

        self.td = TemporaryDirectory()
        self.to_clean_up = ['.dot', '.png', '.gfo']

        # start the GF Repl
        self.gfRepl = GFRepl()
        self.out_count = 0
        self.grammars = self.search_grammars()

        # content handlers
        self.handlers = {
            'MMT_command': self.handle_mmt_command,
            'GF_command': self.gfRepl.handle_gf_command,
            'kernel_command': self.handle_kernel_command
        }

        # load help messages from messages.json file
        messages_path = os.path.dirname(os.path.realpath(__file__))
        try:
            with open(os.path.join(messages_path, 'messages.json')) as f:
                self.messages = load(f)
        except:
            self.messages = None

    def do_shutdown(self):
        """Terminates the GF shell and the MMT subprocess"""
        self.td.cleanup()
        self.gfRepl.do_shutdown()
        self.mmtInterface.do_shutdown()

    # ---------------------------------------------------------------------------- #
    #                           General Content Handling                           #
    # ---------------------------------------------------------------------------- #

    def handle_input(self, code):
        """
            Parses the `code` from the notebook and delegates 
            command handling to the respective handlers

            `code`: str; the user input from the notebook
        """
        messages = []
        parse_dict = parse(code)
        if parse_dict['type']:
            if parse_dict['type'] == 'commands':
                for command in parse_dict['commands']:
                    pipe_commands = command['pipe_commands']
                    pipe_res = []
                    for pipe_command in pipe_commands:
                        pipe_command_type = pipe_command['type']
                        pipe_command_str = pipe_command['command']
                        if pipe_commands.index(pipe_command) == 0:
                            res = self.handlers[pipe_command_type](
                                pipe_command_str)
                            name = get_name(pipe_command_str)

                            lines = res.split('\n')
                            trees = []
                            for line in lines:
                                if line != '' and line != ' ' and line != '\n':
                                    if name == 'parse':
                                        trees.append(line)
                                    pipe_res.append(line)
                        else:
                            # in case the output contains multiple lines
                            new_pipe_res = []
                            for res in pipe_res:
                                new_res = self.handlers[pipe_command_type](
                                    '%s %s' % (pipe_command_str, res))
                                new_pipe_res.append(new_res)
                            pipe_res = new_pipe_res

                    messages.append(to_message_format(trees=trees))

                    for res in pipe_res:
                        if type(res) is dict:
                            messages.append(res)
                        else:
                            messages.append(to_message_format(message=res))

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

    # ---------------------------------------------------------------------------- #
    #                                Kernel Commands                               #
    # ---------------------------------------------------------------------------- #

    def handle_kernel_command(self, command):
        """
            Handles the Kernel-Commands `show`, `clean, `export` and `help`

            'command': str; the command
        """
        name = get_name(command)
        args = get_args(command)

        if name == 'show':
            graph = ' '.join(args)
            return to_message_format(graph=graph)

        elif name == 'clean':
            return self.clean_up()

        elif name == 'export':
            return self.do_export(args[0])

        elif name == 'help':
            if not self.messages:
                return "No help available"
            if args:
                name = args[0]
                if name in GF_commands:
                    return self.gfRepl.handle_gf_command('h %s' % (name))
                if name in self.messages.keys():
                    return self.messages[name]
                else:
                    return "No help available on %s" % (name)
            else:
                return self.messages['help']

    def convert_to_png(self, graph):
        """
            Converts the given `graph` into a png
            Returns the file name of the picture

            `graph`: str
        """
        out_dot = os.path.join(self.td.name, 'out%s.dot' % (self.out_count))
        out_png = os.path.join(self.td.name, 'out%s.png' % (self.out_count))

        with open(out_dot, 'w') as f:
            f.write(graph)

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
        """
            Handles an export command
            Copies the specified Grammar to the current working directory

            `file_name`: str; the name of the file to export
        """
        args = get_args(file_name)
        if len(args) > 1:
            return "export only takes one argument!"
        source_path = os.path.join(
            self.mmtInterface.content_path, self.mmtInterface.archive, 'source')
        files = os.listdir(source_path)
        file_reg = re.compile('^%s.gf$' % (file_name))
        for file in files:
            if file_reg.match(file):
                from shutil import copy2
                copy2(os.path.join(source_path, file), file)
                return 'Exported %s' % (file)
        return 'Could not find %s' % (file_name)

    # ---------------------------------------------------------------------------- #
    #                                 MMT Commands                                 #
    # ---------------------------------------------------------------------------- #

    def handle_mmt_command(self, command):
        """
            Handles the MMT-Commands 'archive', 'construct' and 'subdir'

            'command': str; the command
        """
        name = get_name(command)
        args = get_args(command)
        if name == 'archive':
            if not args:
                tree(self.mmtInterface.get_archive_path())
                return ''
            if len(args) > 1:
                return 'archive takes only one argument!'
            return self.mmtInterface.handle_archive(args[0])

        elif name == 'construct':
            view = None
            if(args[0] == '-v'):
                view = args[1]
                ASTsStr = ' '.join(args[2:])
            else:
                ASTsStr = ' '.join(args)

            h = ASTsStr.split('|')
            ASTs = list(map(str.strip, h))
            return self.mmtInterface.construct(ASTs, view)

        elif name == 'subdir':
            if args and len(args) == 1:
                return self.mmtInterface.create_subdir(args[0])
            elif not args:
                tree(self.mmtInterface.get_cwd(),isFirst=True, displayFullPath=False)
                return ''

    # ---------------------------------------------------------------------------- #
    #                               GF Content                               #
    # ---------------------------------------------------------------------------- #

    def handle_grammar(self, content, name):
        """
            Handles grammar input

            `content`: str; the content of the grammar
            `name`: str; the name of the grammar
        """

        file_name = "%s.gf" % (name)
        file_path = os.path.join(self.mmtInterface.get_cwd(), file_name)
        try:
            with open(file_path, 'w') as f:
                f.write(content)
                f.close()
        except OSError:
            return 'Failed to create grammar %s' % (name)
        out = self.gfRepl.handle_gf_command("import %s" % (file_path))
        if out == 'success':
            build_result = self.mmtInterface.build_file(file_name) # build the Grammar with the GlfBuild extension
            if build_result['isSuccessful']:
                self.grammars[name] = file_path
                return "Defined %s" % (name)
            else:
                return '\n'.join(build_result['errors'])
        return out

    def search_grammars(self):
        grammars = {}
        cwd = self.mmtInterface.get_cwd()
        for file in os.listdir(cwd):
            if file.endswith(".gf"):
                path = os.path.join(cwd, file)
                name = os.path.splitext(file)
                grammars[name] = path
        return grammars
    
    def get_grammars(self):
        return self.grammars
