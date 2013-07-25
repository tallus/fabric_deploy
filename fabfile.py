from __future__ import absolute_import, print_function, unicode_literals
from fabric.api import *
from fabric.contrib.console import confirm

# DO WE NEED THIS?
env.hosts = ['bruno']

code_dir = '/home/paulm/code/rt_scripts/'
repository = 'rtscripts'

def git_status():
    with cd(code_dir):
        result = local("git status -z", capture=True)
        if len(result) != 0:
            abort('Aborting...uncommitted changes or files. Please commit any changes to git')

def git_push(repo=repository):
    with cd(code_dir):
        result = local("git push " + repo)
        if result.failed:
            abort('Aborting...unable to push to repository: ' + repo)

def copy_file_to_server(destfile='ticket_check'):
    put(code_dir + destfile, '/usr/local/bin',  use_sudo=True, mirror_local_mode=True)


    # TODO scp file to server
    # specifying default server, server on command line

def deploy():
    git_status()
    git_push()
    copy_file_to_server()


