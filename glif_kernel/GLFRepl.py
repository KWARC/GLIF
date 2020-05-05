import sys
import os
import subprocess
import signal
import time
import re

from json import load
from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory
from .utils import parse, to_message_format, get_name, get_args, GF_commands, tree, create_nested_dir
from .MMTInterface import MMTInterface
from .GFRepl import GFRepl
from distutils.spawn import find_executable

# TODO maybe get Florian to introduce a MMT-Path
MMT_PATH = os.getenv('MMT_PATH', default=os.path.join(os.path.expanduser('~'), 'MMT'))
GF_PATH = find_executable('gf')


class GLFRepl:

    def __init__(self):
        self.td = TemporaryDirectory()
        self.to_clean_up = ['.dot', '.png', '.gfo']
        # by default save grammars into td
        self.grammar_path = self.td.name
        self.out_count = 0

        self.gfRepl = None
        self.mmtInterface = None

        if GF_PATH:
            # start the GF Repl
            self.gfRepl = GFRepl(GF_PATH)
            
        if os.path.isdir(MMT_PATH):
            # initialize the MMT interface
            self.mmtInterface = MMTInterface(MMT_PATH)
            # in case of MMT installation store grammars in MMT archive
            self.grammar_path = self.mmtInterface.get_cwd()

        self.MMT_blocked = False
        
        self.grammars = self.search_grammars()

        # content handlers
        self.handlers = {
            'MMT_command': self.handle_mmt_command,
            'ELPI_command': self.handle_elpi_command,
            'GF_command': self.handle_gf_command,
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
        if self.gfRepl:
            self.gfRepl.do_shutdown()
        if self.mmtInterface:
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
                            trees = []
                            try: # TODO make this produce a meaningful error message
                                lines = res.split('\n')
                            except:
                                continue
                           
                            for line in lines:
                                if line != '' and line != ' ' and line != '\n':
                                    if name == 'parse' or name == 'p':
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
                messages.append(to_message_format(message=self.handle_grammar(code, parse_dict['name'])))
            elif parse_dict['type'] == 'MMTContent':
                if self.mmtInterface:
                    messages.append(to_message_format(message=self.mmtInterface.create_mmt_file(code, parse_dict['name'], parse_dict['mmt_type'])))
                else:
                    messages.append(to_message_format(message="No MMT installation found. MMT content not available."))
            elif parse_dict['type'] == 'ELPIContent':
                messages.append(to_message_format(message=self.handle_elpi_rules(code, parse_dict['name'])))
        else:
            messages.append(to_message_format(message="Input is neither valid GF or MMT content nor a valid shell command!"))

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

        elif name == 'grammar-path':
            self.grammar_path = create_nested_dir(os.getcwd(), args[0])

            if self.mmtInterface:
                self.MMT_blocked = True
                return "Set grammar-path to %s. MMT functionality is now disabled" % (self.grammar_path)
            
            return "Set grammar-path to %s" % (self.grammar_path)

        elif name == 'help':
            if not self.messages:
                return "No help available"
            if args:
                name = args[0]
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
    #                                 ELPI Commands                                #
    # ---------------------------------------------------------------------------- #

    def handle_elpi_command(self, command):
        args = get_args(command)
        if len(args) < 2:
            return 'ERROR: "elpi" command requires at least 2 arguments (file and rule)'
        if not args[0].endswith('.elpi'):
            args[0] += '.elpi'
        elpi = subprocess.Popen((find_executable('elpi'),
            '-exec',
            args[1],  # predicate
            os.path.join(self.mmtInterface.get_cwd(), args[0]),  # file,
            '--',
            ' '.join(args[2:]),
            ),
            stdin = subprocess.PIPE,
            stderr = subprocess.PIPE,
            stdout = subprocess.PIPE,
            text=True)
        out, err = elpi.communicate()
        if elpi.returncode not in [0,1]:
            return 'ELPI ERROR: ' + str(elpi.returncode) + '\nOUTPUT:\n' + out + '\nERROR:\n' + err
        else:
            return out


    # ---------------------------------------------------------------------------- #
    #                                 MMT Commands                                 #
    # ---------------------------------------------------------------------------- #

    def handle_mmt_command(self, command):
        """
            Handles the MMT-Commands 'archive', 'construct' and 'subdir'

            'command': str; the command
        """
        if not self.mmtInterface:
            return "MMT functionality unavailable. No MMT installation detected."
        
        if self.MMT_blocked:
            return "MMT-functionality is blocked due to changes to the storing location for Grammars with 'grammar-location'."

        name = get_name(command)
        args = get_args(command)
        if name == 'archive':
            if not args:
                # TODO make this into a string so output order doesn't get screwed
                tree(dir=self.mmtInterface.get_archive_path(), archive_name=self.mmtInterface.get_archive())
                return ''
            if len(args) > 1:
                return 'archive takes only one argument!'
            msg = self.mmtInterface.handle_archive(args[0])
            self.grammar_path = self.mmtInterface.get_cwd()
            return msg
        
        if name == 'archives':
            return ', '.join(self.mmtInterface.get_archives())

        elif name == 'construct':
            view = None
            i = 0
            toElpi = False
            while True:
                if args[i] == '-v':
                    view = args[1]
                    i += 2
                elif args[i] == '-elpi':
                    toElpi = True
                    i += 1
                else:
                    break

            ASTsStr = ' '.join(args[i:])

            h = ASTsStr.split('|')
            ASTs = list(map(str.strip, h))
            return self.mmtInterface.construct(ASTs, view, toElpi)

        elif name == 'subdir':
            if args and len(args) == 1:
                msg = self.mmtInterface.create_subdir(args[0])
                self.grammar_path = self.mmtInterface.get_cwd()
                return msg
            elif not args:
                return os.path.relpath(self.mmtInterface.get_cwd(), os.path.join(self.mmtInterface.get_archive_path(), 'source'))

    # ---------------------------------------------------------------------------- #
    #                               GF Content                                     #
    # ---------------------------------------------------------------------------- #

    def handle_gf_command(self, command):
        if not self.gfRepl:
            return "GF functionality unavailable. No GF installation detected."
        return self.gfRepl.handle_gf_command(command)

    def handle_elpi_rules(self, content, name):
        if not name.endswith('.elpi'):
            name += '.elpi'
        file_path = os.path.join(self.grammar_path, name)
        try:
            with open(file_path, 'w') as f:
                f.write('\n'.join(content.splitlines()[1:]))
                f.close()
        except OSError:
            return 'Failed to create grammar %s' % (name)
        return 'Created ' + name

    def handle_grammar(self, content, name):
        """
            Handles grammar input

            `content`: str; the content of the grammar
            `name`: str; the name of the grammar
        """

        file_name = "%s.gf" % (name)
        file_path = os.path.join(self.grammar_path, file_name)
        try:
            with open(file_path, 'w') as f:
                f.write(content)
                f.close()
        except OSError:
            return 'Failed to create grammar %s' % (name)
        out = self.handle_gf_command("import %s" % (file_path))
        if out == 'success' or out.startswith('Abstract changed'):
            if not self.mmtInterface:
                self.grammars[name] = file_path
                return "Defined %s" % (name)

            build_result = self.mmtInterface.build_file(file_name) # build the Grammar with the GlfBuild extension
            if build_result['isSuccessful']:
                self.grammars[name] = file_path
                return "Defined %s" % (name)
            else:
                return '\n'.join(build_result['errors'])
        return out

    def search_grammars(self):
        grammars = {}
        cwd = self.grammar_path
        for file in os.listdir(cwd):
            if file.endswith(".gf"):
                path = os.path.join(cwd, file)
                name = os.path.splitext(file)
                grammars[name] = path
        return grammars
    
    def get_grammars(self):
        return self.grammars
