
import os
import io
import requests

from os.path import join, expanduser, isdir
from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory
from .utils import get_args, generate_port

# TODO maybe introduce env variables for this
MMT_LOCATION = join(expanduser('~'),'MMT')
GLF_BUILD_EXTENSION = 'info.kwarc.mmt.glf.GlfBuildServer'
GLF_CONSTRUCT_EXTENSION = 'info.kwarc.mmt.glf.GlfConstructServer'

# if set to true MMT logs will be printed into the Jupyter Console
LOG_TO_CONSOLE = False

class MMTInterface():

    def __init__(self):
        self.content_path = self.get_content_path()
        # set COMMA/JUPYTER as default archive
        self.archive = 'comma/jupyter'
        self.subdir = None
        self.view = None
    
        # FIXME what does -w do??
        MMT_ARGS = [
            'java', '-jar', join(MMT_LOCATION,'deploy','mmt.jar'), '-w'
        ]

        # start MMT
        if LOG_TO_CONSOLE:
            stdout = None
        else:
            stdout = PIPE
        self.mmt = Popen(MMT_ARGS,preexec_fn=os.setsid,stdin=PIPE, stdout=stdout, text=True, encoding='utf-8')

        self.mmt_port = generate_port()
        # for some reason the mmt shell terminates(??) when additional arguments are supplied
        shell_commands = [
            'extension %s\n' % (GLF_BUILD_EXTENSION),
            'extension %s\n' % (GLF_CONSTRUCT_EXTENSION),
            'build COMMA/GLF gf-omdoc\n',
            'server on %s\n' % (self.mmt_port)
        ]
        for command in shell_commands:
            self.mmt.stdin.write(command)
        self.mmt.stdin.flush()
    
    def do_shutdown(self):
        'Shuts down the MMT server and the MMT shell'
        self.mmt.stdin.write('server off\n')
        self.mmt.communicate('exit\n')[0]
        self.mmt.stdin.close()
        self.mmt.kill()
    
    # ----------------------------- Archive handling ----------------------------- #

    def handle_archive(self, command):
        """
            Handles the archive command:

            args: list; list of arguments
        """
        args = get_args(command)
        if len(args) > 2:
            return 'archive takes at most 2 arguments!'
        if args[0] == '-c':
            return self.create_archive(args[1])
        else:
            name = args[0]
            if isdir(join(self.content_path,name)):
                self.archive = name
                return 'Changed to %s' % (name)
            else:
                return '%s is not a valid archive!' % (name)

    def create_subdir(self, name):
        """Creates a new subdirectory in the current archives src folder"""
        try:
            subdir_path = join(self.content_path, self.archive, 'source', name)
            if isdir(subdir_path):
                self.subdir = name
                return 'Changed to subdirectory %s' % (name)
            os.mkdir(subdir_path)
            self.subdir = name
            return 'Created subdirectory %s' % (name)
        except:
            return 'Creation of subdirectory %s failed! \n' % (name)

    def get_subdir(self):
        """"Returns the current subdirectory"""
        return self.subdir
    
    def change_subdir(self, new):
        """Changes to the new subdirectory"""
        pass


    def create_archive(self, name):
        """
            creates a new archive with the name `name` and sets it as the current archive

            `name`: str; name of the new archive
        """
        # set up the paths
        archive_path = self.content_path
        path, archive = os.path.split(name)
        subdirs = path.split(os.path.sep)
        try:
            for d in subdirs:
                archive_path = join(archive_path, d)
                if isdir(archive_path):
                    continue
                os.mkdir(archive_path)

            archive_path = join(archive_path,archive)
            if isdir(archive_path):
                return '%s already exists!' % (name)
            else:
                os.mkdir(archive_path)
                
            # # create directories
            os.mkdir(join(archive_path, 'META-INF'))
            os.mkdir(join(archive_path, 'source'))
        
            # #create MANIFEST.MF
            with open(join(archive_path,'META-INF', 'MANIFEST.MF'), 'w+') as f:
                f.write('id: %s\nnarration-base: http://mathhub.info/%s' % (self.archive.upper(),self.archive.upper()))
                f.close()
            
        except OSError:
            return('Creation of %s failed! \n%s' % (name, archive_path))
        
        #set it as the current archive
        self.archive = name
        return 'Created %s' % (name)


    # --------------------------- MMT Content Handling --------------------------- #

    def build_file(self, file_name):
        """
            builds gf-omdoc and mmt-omdoc for the current archive and the specified file
            returns a dict of this form:
            {
                isSuccessful: Boolean,
                errors: []
            }
        """
        
        # register the archive in case it was just created
        self.mmt.stdin.write('mathpath archive %s\n' % (join(self.content_path, self.archive)))
        # for some reason MMT archives have to be in upper-case when building them
        j = {
            'archive' : self.archive.upper(),
            'file' : os.path.join(self.subdir, file_name)
        }
        resp = requests.post('http://localhost:%s/:glf-build' % (self.mmt_port), json=j)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {
                'isSuccessful' : False,
                'errors' : ['Communication failed']
            }

    def create_mmt_file(self, content, name, mmt_type):
        """
            Creates a named .mmt file containing either a view or a theory

            `content`: str; content of file

            `name`: str;  name of the file
        
            `mmt_type`: str; type of content, either 'view' or 'theory'
        """

        file_name = '%s.mmt' % name
        file_path = join(self.content_path, self.archive, 'source', self.subdir, file_name)
        try:
            with open(file_path, 'w') as f:
                f.write('namespace http://mathhub.info/%s ❚\n\n' % self.archive.upper())
                f.write(content)
                f.close()
            self.view_name = name
            build_result = self.build_file(file_name)
            if build_result['isSuccessful']:
                if(mmt_type == 'view'):
                    self.view = name
                return 'Created %s %s' % (mmt_type, name)
            else:
                return '\n'.join(build_result['errors'])
        except OSError:
            return 'Failed to create view %s' % name

    
    def handle_construct(self, command):
        """
            Sends a construct request to the MMT GLF server

            `command`: str; the command
        """
        args = get_args(command)
        if(args[0] == '-v'):
            view = args[1]
            self.view = view
            ASTsStr = ' '.join(args[2:])
        else:
            view = self.view
            ASTsStr = ' '.join(args)

        h = ASTsStr.split('|')
        ASTs = list(map(str.strip, h))

        j = {   
            'semanticsView': 'http://mathhub.info/%s/%s' % (self.archive.upper(), view),
            'ASTs': ASTs
        }
        try:
            # apparently requests.post().json() returns a list
            # TODO make this more clear and return a dict like this:
            # {
            #     constructedThingys = [bla, blub, ...]
            # }
            resp = requests.post('http://localhost:%s/:glf-construct' % (self.mmt_port), json=j) 
            
        except:
            return 'Something went wrong during the request'
        if resp.status_code == 200:
            return '\n'.join(resp.json())


    def get_content_path(self):
        """reads the the path to the MMT-content folder from mmtrc and returns it"""
        #TODO maybe find a more elegant solution for this
        try:
            with open(join(MMT_LOCATION,'deploy','mmtrc'),'r') as f:
                # read the 5th line from mmtrc
                for _ in range(5):
                    line = f.readline()
                _, content_path = line.split(' ', 1)
                f.close()
            # remove \n
            return content_path[:-1]
        except OSError:
            return None

