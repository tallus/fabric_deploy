from __future__ import absolute_import, print_function, unicode_literals
from fabric.api import *
from fabric.contrib.console import confirm
import ConfigParser
    
devserver='dev.freegeek.org'

def load_config(config_file = None):
    '''Reads in configuration file.'''
    config = ConfigParser.SafeConfigParser()
    config.optionxform = str
    config.read(config_file)
    configlist = {}
    for section in config.sections():
        configlist[section] = {}
        for name, value in config.items(section):
            configlist[section].update({name: value})
    return configlist

def create_remote_git_repository(repo. desc = None):
    if not desc:
        desc = prompt("Please enter a project description")
    env.hosts = [devserver]
    result = run("/usr/local/bin/create_project  -u paulm -l support-staff -d " + description  + " ts_" + repo)
    if result.failed:
        abort('Aborting...unable to create remote repository: ' + 'ts_' + ssh://repo)


def git_status(code_dir=srcdir):
    with cd(code_dir):
        result = local("git status -z", capture=True)
        if len(result) != 0:
            abort('Aborting...uncommitted changes or files. Please commit any changes to git')

def git_push(repo=repository,code_dir=srcdir):
    with cd(code_dir):
        result = local("git push " + repo)
        if result.failed:
            abort('Aborting...unable to push to repository: ' + repo)

def copy_file_to_server(srcfile, destdir, destfile=None):
    put(code_dir + destfile, destdir, use_sudo=True, mirror_local_mode=True)

def test_remote_dir(rdir):
    result = run("ls " + rdir, quiet=True)
    if result.failed and not confirm("Remote directory: " + rdir + 
            " does not exist, create it?"):
        abort("Remote directory does not exist")
    else:
        create_remote_dir(rdir)

def create_remote_dir(rdir):
    result = sudo ("mkdir -p " + rdir, quiet=True)
    if result.failed:
        abort('Could not create remote directory: ' + rdir)

def predeploy():
    git_status()
    git_push()

def resolve_dependencies(aptlist=None, piplist=None):
    aptlist = "".join(aptlist)
    piplist = "".join(piplist)
    if aptlist:
        sudo("apt-get update")
        result = sudo("apt-get install -y " + aptlist)
        if result.failed:
            abort('could not install required deb packages on' + env 
    if piplist:
        sudo("pip-get update")
        result = sudo("pip install  " + piplist)
        if result.failed:
            abort('could not install required python packages on' + env 
    
def deploy(source_files=None, remote_dir=None):
    if  not source_files:
        source_files = srcfiles
    source_files = source_files.split(',')
    if not source_files:
        abort('No source files supplied')
    if not remote_dir:
        if destdir:
            remote_dir = destdir
        else:
            remote_dir = '/usr/local/bin'
    test_remote_dir(remote_dir)
    predeploy()
    resolve_dependencies(aptlist, piplist)
    
    # TODO set dest dir and remote file names
    # TODO loop over source files
    copy_file_to_server()



# Set config
config = load_config('fab.cfg')
network_config = config['network']
# allow overiding on the command line with --hosts
if not env.hosts:
    hostlist = network_config['hosts'].split(',')
    env.hosts = hostlist
else:
    hostlist = env.hosts
local_config = config['local']
# these can not be overridden
srcdir =  local_config['source_dir']
repository = local_config['repository']
# this can be overridden by specifying it as an option
# to deploy e.g. fab deploy:source_files='file'
srcfiles = local_config['srcfiles']
remote_config = config['remote']
# this can be overridden by specifying it as an option
# to deploy e.g. fab deploy:remote_dir='/path/to/dir'
destdir = remote_config['remote_dir']
depend_config = config['dependencies']
aptlist = depend_config['apt'].split(',')
piplist = depend_config['pip'].split(',')

