import sys
import os
from subprocess import Popen, PIPE, STDOUT



class GFRepl:
    importList = []

    def __init__(self, GF_BIN, GF_LIB):
        self.GF_ARGS = [
            GF_BIN, 
            '--run', 
            '--gf-lib-path=%s' %(GF_LIB),
        ]

    def handle_input(self, code):
        """Sends the `code` to the GF shell""" 
        # we save all imports and send them with every command
        if code.startswith('import'):
            _,grammar = code.split(' ',1)
            # check if we can actually import it
            p = Popen(self.GF_ARGS, stdin=PIPE, stdout=PIPE)
            resp = p.communicate(code.encode())[0].decode()
            if resp:
                return resp.replace('\n','').replace('ExitFailure 1', '') # get rid of the the newlines and the ExitFailure 1 
            self.importList.append(grammar)
            return "Successfully imported %s" % (grammar)
        else:
            p = Popen(self.GF_ARGS, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
            command = self.build_full_command(code)
            return p.communicate(command.encode())[0].decode().replace('\n','') # get rid of the newlines
    
    # TODO look at how multiple imports are done
    def build_full_command(self, code):
        """Builds the full command including all imports"""
        c = 'import'
        for grammar in self.importList:
            c += ' %s' % (grammar) 
        return "%s\n%s\n" % (c, code)

    def start(self):
        """Starts the REPL"""
        i = sys.stdin.readline()
        while i and i != 'quit\n':
            print(self.handle_input(i))
            i = sys.stdin.readline()


# if __name__ == '__main__':
#     repl = GFRepl('.','.')
#     repl.start()



