import sys
import os
import signal
import time
import re 

from subprocess import PIPE, Popen
from .utils import readFile, parse, parse_command, to_message_format

class GFRepl:

    def __init__(self, GF_BIN, GF_LIB):

        self. GF_BIN = GF_BIN
        self.GF_LIB = GF_LIB

        GF_ARGS = [
            GF_BIN, 
            '--run', 
            '--gf-lib-path=%s' %(GF_LIB),
        ]

        self.out_file_name = 'shell.out'
        self.to_clean_up = ['.png','.gfo','.dot']
        self.out = open(self.out_file_name, 'w+')
        self.shell = Popen(GF_ARGS, stdin=PIPE, stdout=self.out, stderr=self.out)
        self.pid = os.getpid()
        self.out_count = 0
        
        # register the signal handler for the notify process
        signal.signal(signal.SIGUSR1, self.signal_handler)

    def do_shutdown(self):
        self.handle_shell_input('q')
        self.clean_up()
        self.shell.communicate()[0]
        self.shell.stdin.close()
        self.shell.kill()

    def handle_input(self,code):
        messages = []
        # ret_dict = {
        #     'messages' : [],
        #     'files' : []
        # }
        parse_dict = parse(code)
        if parse_dict['type']:
            if parse_dict['type'] == 'commands':
                for command in parse_dict['commands']:
                    name = command['name']
                    args = command['args']
                    if name == 'view':
                        messages.append(self.handle_multiple_view(command['args']))
                    elif name == 'clean': 
                        messages.append(to_message_format(message=self.clean_up()))
                    else:
                        cmd = '%s %s' % (name, args)
                        msg = self.handle_shell_input(cmd)
                        if name == 'import' and not msg:
                            messages.append(to_message_format(message='Import successful!'))
                        else:
                            messages.append(to_message_format(message=msg))
            else:
                messages.append(to_message_format(message=self.handle_grammar(code,parse_dict['grammar_name'])))
              
        else:
            messages.append(to_message_format(message="Input is neither a valid grammar nor a valid gf shell command!"))

        return messages
    
    def handle_grammar(self, grammar, name):
        file_path = os.path.join(self.GF_LIB,"%s.gf" % (name))
        with open(file_path, 'w') as f:
            f.write(grammar)
            f.close()
        out = self.handle_shell_input("import %s.gf" % (name))
        if not out:
            out = "Defined %s" % (name)
        return out
    



    def handle_multiple_view(self,command):
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
                return to_message_format(trees=trees,tree_type=cmd['tree_type'])

        return to_message_format(file=self.handle_single_view(command))


    def handle_single_view(self, command):
        out_dot = 'out%s.dot' % (self.out_count)
        out_png = 'out%s.png' % (self.out_count)
        cmd = '%s | wf -file=%s' % (command, out_dot)
        self.handle_shell_input(cmd)
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
        cmd ='sp -command=\"python %s/notify.py %s\"\n' % (os.path.dirname(os.path.abspath(__file__)), self.pid)
        self.shell.stdin.write(cmd.encode())
        self.shell.stdin.flush()

        signal.pause() # wait for the shell to finish

        # self.out.close()
        time.sleep(0.2)
        out = readFile(self.out_file_name,cp_s).replace('ExitFailure 1','') 
        
        return out

    def clean_up(self):
        removed = []
        for root, _, files in os.walk("."):
            for file in files:
                file_path = os.path.join(root, file)
                _, file_extension = os.path.splitext(file_path)
                if file_extension in self.to_clean_up:
                    os.remove(file_path)
                    removed.append(file_path)
        msg = ''
        for f in removed:
            msg += 'Removed %s\n' % (f)
        self.out_count = 0
        return msg

    def start(self):
        """Starts the REPL"""
        i = sys.stdin.readline()
        while i and i != 'quit\n' and i != 'q\n':
            print(self.handle_shell_input(i[:-1])) # send input with out the newline
            i = sys.stdin.readline()
    

    def signal_handler(self, signum, frame):
        """Signal handler for the notify process"""
        pass


    

if __name__ == '__main__':
    repl = GFRepl('/usr/bin/gf', os.path.expanduser('~'))
    repl.start()



