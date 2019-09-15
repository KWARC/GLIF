
import os
import io
import requests

from os.path import join, expanduser, isdir
from subprocess import PIPE, Popen
from IPython.utils.tempdir import TemporaryDirectory

# TODO maybe introduce env variables for this
MMT_DEPLOY_LOCATION = join(expanduser('~'),'MMT','deploy')

class MMTInterface():

    def __init__(self):
        self.content_path = self.get_content_path()
        # set COMMA/JUPYTER as default archive
        self.archive = 'comma/jupyter'
        self.view = None
    
        # FIXME what does -w do??
        MMT_ARGS = [
            "java", "-jar", join(MMT_DEPLOY_LOCATION,'mmt.jar'), '-w'
        ]

        # start MMT
        self.mmt = Popen(MMT_ARGS,preexec_fn=os.setsid,stdin=PIPE, text=True, encoding='utf-8')
        # for some reason the mmt shell terminates(??) when additional arguments are supplied
        self.mmt.stdin.write('extension info.kwarc.mmt.gf.GfImporter\n')
        self.mmt.stdin.write('extension info.kwarc.mmt.glf.GlfServer\n')
        self.mmt.stdin.write('build COMMA/GLF gf-omdoc\n')
        self.mmt.stdin.write('server on 8080\n')
        self.mmt.stdin.flush()
    
    def handle_archive(self, args):
        """
            Handles the archive command:

            args: list; list of arguments
        """
        if args[0] == '-c':
            return self.create_archive(args[1])
        else:
            return self.change_and_build_archive(args[0])


    def change_and_build_archive(self, name):
        """
            Checks if the specified archive exists and sets it as current archive.
            Also builds the archive.

            `name`: str; name of the archive to switch to
        """
        if isdir(join(self.content_path,name)):
            self.archive = name
            self.build_archive()
            return "Changed to %s" % (name)
        else:
            return "%s is not a valid archive!" % (name)

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
        
    def create_mmt_file(self, content, name, mmt_type):
        """
            Creates a named .mmt file containing either a view or a theory

            `content`: str; content of the view

            `name`: str;  name of the view
        
            `mmt_type`: str; type of content, either 'view' or 'theory'
        """

        view_path = join(self.content_path, self.archive, 'source', '%s.mmt' % name)
        try:
            with open(view_path, 'w') as f:
                f.write('namespace http://mathhub.info/%s ❚\n\n' % self.archive.upper())
                f.write(content)
                f.close()
            self.view_name = name
            self.build_archive()
            if(mmt_type == 'view'):
                self.view = name
            return 'Created %s %s' % (mmt_type, name)
        except OSError:
            return 'Failed to create view %s' % name

    def get_content_path(self):
        """reads the the path to the MMT-content folder from mmtrc and returns it"""
        #TODO maybe find a more elegant solution for this
        try:
            with open(join(MMT_DEPLOY_LOCATION,'mmtrc'),'r') as f:
                for _ in range(5):
                    line = f.readline()
                _, content_path = line.split(' ', 1)
                f.close()
            return content_path[:-1]
        except OSError:
            return None
    
    def build_archive(self):
        """builds gf-omdoc and mmt-omdoc for the current archive"""
        # register the archive in case it was just created
        self.mmt.stdin.write('mathpath archive %s\n' % (join(self.content_path, self.archive)))
        # for some reason MMT archives have to be in upper-case when building them
        self.mmt.stdin.write('build %s gf-omdoc\n' % (self.archive.upper()))
        self.mmt.stdin.write('build %s mmt-omdoc\n' % (self.archive.upper()))
        self.mmt.stdin.flush()
    
    def do_shutdown(self):
        "Shuts down the MMT server and the MMT shell"
        self.mmt.stdin.write('server off\n')
        self.mmt.communicate('exit\n')[0]
        self.mmt.stdin.close()
        self.mmt.kill()
    
    def handle_request(self, args):
        """
            Sends a request to the MMT GLF server

            `args`: list; list of arguments
        """

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
            "semanticsView": "http://mathhub.info/%s/%s" % (self.archive.upper(), view),
            "ASTs": ASTs
        }
        try:
            resp = requests.post("http://localhost:8080/:glf", json=j)
        except:
            return "Something went wrong during the request"
        if resp.status_code == 200:
            return resp.text