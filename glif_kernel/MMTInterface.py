
import os
import io
import requests
import time

from os.path import join, expanduser, isdir
from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory
from .utils import get_args, generate_port, create_nested_dir

GLF_BUILD_EXTENSION = 'info.kwarc.mmt.glf.GlfBuildServer'
GLF_CONSTRUCT_EXTENSION = 'info.kwarc.mmt.glf.GlfConstructServer'
ELPI_GENERATION_EXTENSION = 'info.kwarc.mmt.glf.ElpiGenerationServer'

# if set to true MMT logs will be printed into the Jupyter Console
LOG_TO_CONSOLE = False


class MMTInterface():

    def __init__(self, MMT_PATH):
          # start MMT
        if LOG_TO_CONSOLE:
            stdout = None
        else:
            stdout = PIPE

        MMT_ARGS = [
            'java', '-jar', join(MMT_PATH, 'deploy', 'mmt.jar'), '-w'  # FIXME what does -w do??
        ]
        self.mmt = Popen(MMT_ARGS, stdin=PIPE, stdout=stdout, text=True, encoding='utf-8')
        self.mmt_port = generate_port()
        # for some reason the mmt shell terminates(??) when additional arguments are supplied
        shell_commands = [
            'extension %s\n' % (GLF_BUILD_EXTENSION),
            'extension %s\n' % (GLF_CONSTRUCT_EXTENSION),
            'extension %s\n' % (ELPI_GENERATION_EXTENSION),
            'server on %s\n' % (self.mmt_port)
        ]
        for command in shell_commands:
            self.mmt.stdin.write(command)
        self.mmt.stdin.flush()
        time.sleep(2)    # TODO: Better way to determine whether everything has started!

        self.mmt_path = MMT_PATH
        self.content_path = self.do_get_content_path()
        self.archives = find_archives(self.content_path)
        self.archive = 'comma/jupyter' # set COMMA/JUPYTER as default archive
        self.handle_archive(self.archive) 
        self.subdir = ''
        self.view = None
      

    def do_shutdown(self):
        """Shuts down the MMT server and the MMT shell"""
        self.mmt.stdin.write('server off\n')
        self.mmt.communicate('exit\n')[0]
        self.mmt.stdin.close()
        self.mmt.kill()
    
    def get_content_path(self):
        return self.content_path
    
    def get_archive_path(self):
        return join(self.content_path, self.archives[self.archive])

    def get_cwd(self):
        return join(self.content_path, self.archives[self.archive], 'source', self.subdir)
    
    def get_archive(self):
        return self.archive
    
    def get_archives(self):
        return self.archives.keys()
    

    # ----------------------------- Archive handling ----------------------------- #

    def handle_archive(self, name):
        if name in self.archives.keys(): # archive already exists
            self.archive = name
            self.subdir = '' # reset subdir
            return 'Changed to archive %s' % (name)

        try:
            os_path = name.replace('/', os.path.sep) # replace '/' by '\' when on windows
            archive_path = create_nested_dir(self.content_path, os_path)
            os.mkdir(join(archive_path, 'META-INF'))
            os.mkdir(join(archive_path, 'source'))

            with open(join(archive_path, 'META-INF', 'MANIFEST.MF'), 'w+') as f:
                f.write('id: %s\nnarration-base: http://mathhub.info/%s' % (name, name))
                f.close()
            
            p = join(self.content_path, os_path).replace('\\','/') # the archive path has to be in Unix format to work
            self.mmt.stdin.write('mathpath archive %s\n' % (p)) # register the archive in MMT
            self.mmt.stdin.flush()
            self.archive = name
            self.subdir = '' # reset subdir

            self.archives.update({name : os_path})
            
            return 'Created archive %s' % (name)

        except OSError as e:
            return('Creation of %s failed: %s' % (name, e.strerror))

    # --------------------------- Subdirectory handling -------------------------- #

    def create_subdir(self, name):
        """
            Creates a new subdirectory in the current archives src directory.
            All created subdirectories created relative to the archives source directory.

            `name`: str; name of the subdirectory (e.g. "test1/test1_1")
        """
        if name == '..':
            return 'Cannot go above the source directory!'

        os_path = name.replace('/',os.path.sep).replace('\\',os.path.sep)

        source_path = join(self.get_archive_path(), 'source')
        subdir_path = join(source_path, os_path)

        
        if isdir(subdir_path):
            self.subdir = name
            return 'Changed to subdirectory %s' % (name)
        try:
            create_nested_dir(source_path, os_path) 
            self.subdir = name
            return 'Created subdirectory %s' % (name)
        except OSError as e:
            return 'Creation of subdirectory %s failed: %s \n' % (name,  e.strerror)

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
        file_ = file_name
        if self.subdir:
            file_ = '/'.join([self.subdir, file_name]) # MMT needs file paths in Linux format
        j = {
            'archive': self.archive,
            'file': file_,
        }
        resp = requests.post('http://localhost:%s/:glf-build' %
                             (self.mmt_port), json=j)
        if resp and resp.status_code == 200:
            try:
                return resp.json()
            except:
                return {
                    'isSuccessful': False,
                    'errors': [resp.text]
                }
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
        file_path = join(self.get_archive_path(), 'source', self.subdir, file_name)
        try:
            with io.open(file_path, 'w', encoding='utf-8',) as f:
                f.write('namespace http://mathhub.info/%s ❚\n\n' %
                        self.archive)
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
            return 'Failed to create %s' % name

    def construct(self, ASTs, v=None, toElpi=False):
        """
            Sends a construct request to the MMT GLF server

            `command`: str; the command
        """
        if v:
            self.view = v

        j = {
            'semanticsView': 'http://mathhub.info/%s/%s' % (self.archive, self.view),
            'ASTs': ASTs,
            'toElpi' : toElpi,
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
            try:
                return '\n'.join(resp.json())
            except:
                return resp.text

    def elpigen(self, mode, theory, targetName, meta=False, includes = True):
        j = {
                'theory' : 'http://mathhub.info/%s/%s' % (self.archive, theory),
                'mode' : mode,
                'follow-meta' : meta,
                'follow-includes' : includes,
        }
        try:
            resp = requests.post(
                'http://localhost:%s/:glif-elpigen' % (self.mmt_port), json=j)
        except:
            return 'Something went wrong during the request'
        # (success, result)
        try:
            return (True, resp.json())
        except:
            return (False, resp.text)




    def do_get_content_path(self):
        """reads the the path to the MMT-content folder from mmtrc and returns it"""
        # TODO maybe find a more elegant solution for this
        # try:
        with open(join(self.mmt_path, 'deploy', 'mmtrc'), 'r') as f:
            for _ in range(5): # read the 5th line from mmtrc
                line = f.readline()
            _, content_path = line.split(' ', 1)
            f.close()
            return content_path.strip()
        # except OSError:
        #     return None



def find_archives(dir, base_dir=None):
    """
        Searches the directory `dir` recursively for archive directories.
        
        `dir` : absulute path to the starting directory
        `base_dir` : the base directory for the output paths

        Returns a dict like this:
        {
            `archive_name` : path to this archive relative to `base_dir`
        }
    """
    if not base_dir:
        base_dir = dir
    if is_archive(dir):
        return {
            get_archive_name(dir) : os.path.relpath(dir, base_dir)
        }
    else:
        res = {}
        subdirs = os.listdir(dir)
        for f in subdirs:
            path = os.path.join(dir, f)
            if os.path.isdir(path):
                res.update(find_archives(path, base_dir))
        return res
                    
def is_archive(dir):
    """"Checks if `dir` contains a 'META-INF' and 'source' directory."""
    subdirs = os.listdir(dir)
    if not subdirs:
        return False
    has_META_INF = False
    has_source = False
    for subdir_name in subdirs:
        subdir_path = join(dir, subdir_name)
        if os.path.isdir(subdir_path):
            if subdir_name == 'META-INF':
                has_META_INF = True
                continue
            if subdir_name == 'source':
                has_source = True
    
    return has_META_INF and has_source

def get_archive_name(dir):
    """Reads the MMT archive name from the MANIFEST.MF file"""
    try:
        with open(join(dir, 'META-INF', 'MANIFEST.MF'), 'r+') as f:
            line = f.readline()
            _, archive_name = line.split(' ')
            f.close()
        return archive_name.strip()
    except:
        return None




    
