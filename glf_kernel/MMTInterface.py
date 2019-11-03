
import os
import io
import requests

from os.path import join, expanduser, isdir
from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory
from .utils import get_args, generate_port, create_nested_dir

# TODO maybe introduce env variables for this or get Florian to introduce a MMT-Path
MMT_LOCATION = join(expanduser('~'), 'MMT')
GLF_BUILD_EXTENSION = 'info.kwarc.mmt.glf.GlfBuildServer'
GLF_CONSTRUCT_EXTENSION = 'info.kwarc.mmt.glf.GlfConstructServer'

# if set to true MMT logs will be printed into the Jupyter Console
LOG_TO_CONSOLE = False


class MMTInterface():

    def __init__(self):
        self.content_path = do_get_content_path()
        # set COMMA/JUPYTER as default archive
        self.archive = 'comma/jupyter'
        self.subdir = ''
        self.view = None
       
        MMT_ARGS = [
            'java', '-jar', join(MMT_LOCATION, 'deploy', 'mmt.jar'), '-w'  # FIXME what does -w do??
        ]

        # start MMT
        if LOG_TO_CONSOLE:
            stdout = None
        else:
            stdout = PIPE
        self.mmt = Popen(MMT_ARGS, stdin=PIPE,
                         stdout=stdout, text=True, encoding='utf-8')

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
        """Shuts down the MMT server and the MMT shell"""
        self.mmt.stdin.write('server off\n')
        self.mmt.communicate('exit\n')[0]
        self.mmt.stdin.close()
        self.mmt.kill()
    
    def get_content_path(self):
        return self.content_path
    
    def get_archive_path(self):
        return join(self.content_path, self.archive)

    def get_cwd(self):
        return join(self.content_path, self.archive, 'source', self.subdir)
    

    # ----------------------------- Archive handling ----------------------------- #

    def handle_archive(self, name):
        archive_path = join(self.content_path, name)
        if isdir(archive_path):  # archive already exists
            self.archive = name
            self.subdir = '' # reset subdir
            return 'Changed to archive %s' % (name)

        try:
            create_nested_dir(self.content_path, name)
            os.mkdir(join(archive_path, 'META-INF'))
            os.mkdir(join(archive_path, 'source'))

            with open(join(archive_path, 'META-INF', 'MANIFEST.MF'), 'w+') as f:
                f.write('id: %s\nnarration-base: http://mathhub.info/%s' %
                        (name.upper(), name.upper()))
                f.close()
            
            # register the archive in MMT
            self.mmt.stdin.write('mathpath archive %s\n' % (join(self.content_path, self.archive)))
            self.archive = name
            self.subdir = '' # reset subdir
            
            return 'Created archive %s' % (name)

        except OSError:
            return('Creation of %s failed! \n%s' % (name, archive_path))

    # --------------------------- Subdirectory handling -------------------------- #

    def create_subdir(self, name):
        """
            Creates a new subdirectory in the current archives src folder

            `name`: str; name of the subdirectory (e.g. "test1/test1_1")
        """
        source_path = join(self.content_path, self.archive, 'source')
        subdir_path = join(source_path, name)

        try:
            if isdir(subdir_path):
                self.subdir = name
                return 'Changed to subdirectory %s' % (name)

            create_nested_dir(source_path, name)
            self.subdir = name
            return 'Created subdirectory %s' % (name)
        except:
            return 'Creation of subdirectory %s failed! \n' % (name)

    def get_subdir(self):
        return self.subdir

    # --------------------------- MMT Content Handling --------------------------- #

    def build_file(self, file_name):
        """
            Builds gf-omdoc and mmt-omdoc for the current archive and the specified file.
            Returns a dict of this form:
            {
                isSuccessful: Boolean,
                errors: []
            }

            `file_name`: str; name of the file
        """
        # for some reason MMT archives have to be in upper-case when building them
        j = {
            'archive': self.archive.upper(),
            'file': os.path.join(self.subdir, file_name)
        }
        resp = requests.post('http://localhost:%s/:glf-build' %
                             (self.mmt_port), json=j)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {
                'isSuccessful': False,
                'errors': ['Communication failed']
            }

    def create_mmt_file(self, content, name, mmt_type):
        """
            Creates a named .mmt file containing either a view or a theory

            `content`: str; content of file

            `name`: str;  name of the file

            `mmt_type`: str; type of content, either 'view' or 'theory'
        """

        file_name = '%s.mmt' % name
        file_path = join(self.content_path, self.archive,
                         'source', self.subdir, file_name)
        try:
            with io.open(file_path, 'w', encoding='utf-8',) as f:
                f.write('namespace http://mathhub.info/%s ❚\n\n' %
                        self.archive.upper())
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

    def construct(self, ASTs, v=None):
        """
            Sends a construct request to the MMT GLF server

            `command`: str; the command
        """
        if v:
            self.view = v

        j = {
            'semanticsView': 'http://mathhub.info/%s/%s' % (self.archive.upper(), self.view),
            'ASTs': ASTs
        }
        try:
            # apparently requests.post().json() returns a list
            # TODO make this more clear and return a dict like this:
            # {
            #     constructedThingys = [bla, blub, ...]
            # }
            resp = requests.post(
                'http://localhost:%s/:glf-construct' % (self.mmt_port), json=j)

        except:
            return 'Something went wrong during the request'
        if resp.status_code == 200:
            return '\n'.join(resp.json())


def do_get_content_path():
    """reads the the path to the MMT-content folder from mmtrc and returns it"""
    # TODO maybe find a more elegant solution for this
    try:
        with open(join(MMT_LOCATION, 'deploy', 'mmtrc'), 'r') as f:
            for _ in range(5): # read the 5th line from mmtrc
                line = f.readline()
            _, content_path = line.split(' ', 1)
            f.close()
        return content_path[:-1]  # remove \n
    except OSError:
        return None
