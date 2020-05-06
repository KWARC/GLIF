import os
import subprocess
from distutils.spawn import find_executable
from .utils import get_name, get_args


# Basically a unique string that will never show up in the output (hopefully)
COMMAND_SEPARATOR = "COMMAND_SEPARATOR===??!<>239'_"

class GFRepl(object):
    def __init__(self, GF_PATH, cwd=None):
        self.pipe = os.pipe()
        self.gf_shell = subprocess.Popen((GF_PATH, '--run'),
                          stdin = subprocess.PIPE,
                          stderr = self.pipe[1],
                          stdout = self.pipe[1],
                          text = True,
                          cwd=cwd)
        self.commandcounter = 0
        self.infile = os.fdopen(self.pipe[0])

        # catch any initial messages
        sep = self.write_separator()
        self.gf_shell.stdin.flush()
        self.initialOutput = self.get_output(sep)

    def write_cmd(self, cmd):
        if not cmd.endswith('\n'):
            cmd += '\n'
        self.gf_shell.stdin.write(cmd)
        self.commandcounter += 1

    def write_separator(self):
        sep = COMMAND_SEPARATOR + str(self.commandcounter)
        self.gf_shell.stdin.write(f"ps \"{sep}\"\n")
        return sep

    def get_output(self, sep):
        """Reads lines until sep found"""
        output = ""
        for line in self.infile:
            if line.rstrip() == sep:
                return output
            if line != '\n':  # ignore empty lines
                output += line

    def handle_gf_command(self, cmd):
        """Forwards a command to the GF Shell and returns the output"""
        cmd_name = get_name(cmd)
        self.write_cmd(cmd)
        sep = self.write_separator()
        self.gf_shell.stdin.flush()
        res = self.get_output(sep).strip()
        if cmd_name == "import" and not res:
            return "success"
        return res
        

    def do_shutdown(self):
        """Terminates the GF shell. """
        self.gf_shell.communicate('q\n')[0]
        self.gf_shell.stdin.close()
        self.gf_shell.kill()


if __name__ == "__main__":
    import sys
    gfrepl = GFRepl(find_executable('gf'))
    print(gfrepl.initialOutput)
    while True:
        line = input("> ")
        print(gfrepl.handle_gf_command(line))
