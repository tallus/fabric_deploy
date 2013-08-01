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

def copy_file_to_server(srcfile, dest):
    put(code_dir + srcfile, dest, use_sudo=True, mirror_local_mode=True)

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
    aptlist = " ".join(aptlist)
    piplist = " ".join(piplist)
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
    # check to see if there is per host configuration
    if config[env.host]:
        remote_config = config[env.host]
    if remote_config['remote_dir']:
            remote_dir = remote_config['remote_dir']
        else:
            remote_dir = '/usr/local/bin/'
    # addend / to remote_dir if needed
    if remote_dir[len(remote_dir) - 1] != '/':
        remote_dir = remote_dir + '/'
    # check to see if remote_dir exists
    test_remote_dir(remote_dir)
    # check git is up to date
    predeploy()
    resolve_dependencies(aptlist, piplist)
    # copy source files
    for f in source_files:
        if remote_config[f]:
            name = remote_config[f]
            # if absolute path is not specified prepend remote_dir
            if name[0] != '/':
                name = remote_dir + name
        if name:
            copy_file_to_server(f, name)
        else:
            copy_file_to_server(f, remote_dir)




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
srcfiles = local_config['srcfiles'].split(',')
depend_config = config['dependencies']
aptlist = depend_config['apt'].split(',')
piplist = depend_config['pip'].split(',')

# Note this will be overrriden by any host specific configuration
# see example fab.cfg file
remote_config = config['remote']
