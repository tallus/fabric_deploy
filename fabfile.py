'''Generic fabfile for use with fab.cfg'''
from __future__ import absolute_import, print_function, unicode_literals
from fabric.api import *
from fabric.contrib.console import confirm
import ConfigParser
    
DEVSERVER = 'dev.freegeek.org'
USER = 'paulm'
LIST = 'support-staff'

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

def create_remote_git_repository(repo=REPOSITORY, desc = None):
    '''Creates a git repostiroy of the DEVSERVER'''
    if not desc:
        desc = prompt("Please enter a project description")
    env.hosts = [DEVSERVER]
    result = run("/usr/local/bin/create_project  -u " + USER 
        + " -l " + LIST + " -d " + desc  + " ts_" + repo)
    if result.failed:
        abort('Aborting...unable to create remote repository: ' 
                + 'ts_' + repo)
    return result

def git_status(code_dir=SRCDIR):
    '''run git status locally, abort if not up todate'''
    with cd(code_dir):
        result = local("git status -z", capture=True)
        if result:
            abort("Aborting...uncommitted changes or files.\
                    Please commit any changes to git")
    return result

def git_push(repo=REPOSITORY, code_dir=SRCDIR):
    '''push git repo, abort on fail'''
    with cd(code_dir):
        result = local("git push " + repo)
        if result.failed:
            abort('Aborting...unable to push to repository: ' + repo)
    return result

def copy_file_to_server(srcfile, dest):
    ''' copy a file to the relevant directory on the remote server'''
    result = put(srcfile, dest, use_sudo=True, mirror_local_mode=True)
    if result.failed:
        abort("Aborting...unable to copy %s to %s on %s" 
            %(srcfile, dest, env.host)) 
    return result

def test_remote_dir(rdir):
    '''test to see if a remote directroy exists. Prompt user
    if it is not'''
    result = run("ls " + rdir, quiet=True)
    if result.failed and not confirm("Remote directory: " + rdir + 
            " does not exist, create it?"):
        abort("Remote directory does not exist")
    else:
        create_remote_dir(rdir)
    return result

def create_remote_dir(rdir):
    '''create directory on remote server'''
    result = sudo ("mkdir -p " + rdir, quiet=True)
    if result.failed:
        abort('Could not create remote directory: ' + rdir)
    return result


def predeploy():
    '''ensure git is up to date  prior to deployment'''
    git_status()
    git_push()

def get_deb_dependencies(config, role=None):
    '''returns lists of deb packages to install'''
    if config['role']:
        dependconfig=config['role']
        if dependconfig['apt']:
            aptlist = dependconfig['apt'].split(',')
        else:
            dependconfig = config['dependencies']
            aptlist = dependconfig['apt'].split(',')
     else:
        dependconfig = config['dependencies']
        aptlist = dependconfig['apt'].split(',')
    aptlist = " ".join(aptlist)
    return aptlist

def get_pip_dependencies(config, role=None):
    '''returns lists of python packages to install'''
    if config['role']:
        dependconfig=config['role']
        if dependconfig['pip']:
            piplist = dependconfig['pip'].split(',')
        else:
            dependconfig = config['dependencies']
            piplist = dependconfig['pip'].split(',')
     else:
        dependconfig = config['dependencies']
        piplist = dependconfig['pip'].split(',')
    piplist = " ".join(piplist)
    return piplist

def install_deb_dependencies(aptlist):
    '''install required deb packages'''
    sudo("apt-get update")
    result = sudo("apt-get install -y " + aptlist)
    if result.failed:
        abort('could not install required deb packages on ' + env.host)
    return result

def install_pip_dependencies(piplist):
    '''install required python packages'''
    result = sudo("pip install  " + piplist)
    if result.failed:
        abort('could not install required python packages on' + env.host) 
    return result

def resolve_dependencies(config, role=None):    
    '''install debs / python packages on remote server as needed'''
    aptlist = get_deb_dependencies(config, role)
    if aptlist:
        install_deb_dependencies(aptlist) 
    piplist = get_deb_dependencies(config, role)
    if piplist:
        install_pip_dependencies(piplist) 

def get_remote_dir(role=None):
    '''returns the remote directory to use'''
    # check to see if there is per host configuration
    if CONFIG[env.host]:
        remote_config = CONFIG[env.host]
    elif CONFIG[role]:
        remote_config = CONFIG[role]
    else:
        remote_config = CONFIG['remote']
    if remote_config['remote_dir']:
        remote_dir = remote_config['remote_dir']
    else:
        remote_dir = '/usr/local/bin/'
    # addend / to remote_dir if needed
    if remote_dir[len(remote_dir) - 1] != '/':
        remote_dir = remote_dir + '/'
    return remote_dir

def get_dest(remotedir, srcfile, role=None):
    '''returns destination path/name'''
    # check to see if there is per host configuration
    if CONFIG[env.host]:
        remote_config = CONFIG[env.host]
    elif CONFIG[role]:
        remote_config = CONFIG[role]
    else:
        remote_config = CONFIG['remote']
    if remote_config[srcfile]:
        dest = remote_config[srcfile]
        # if absolute path is not specified prepend remote_dir
        if dest[0] != '/':
            dest = remotedir + dest
    else:
        dest = remotedir
    return dest

def get_source(srcfile):
    '''return path of sourcefile'''
    if SRCDIR:
        source = SRCDIR + '/' + srcfile
    else:
        source = srcfile
    return source


def get_hosts(srcfile):
    '''get list of hosts to install file on, using roles???'''
    pass

def get_srcfiles(config=CONFIG, role=None):
    '''get list of srcfiles'''
        source_files = SRCFILES
        source_files = source_files.split(',')
    if not source_files:
        abort('No source files supplied')
    pass

def deploy_file(srcfile, role=None):
    '''deploy individual file'''
    source = get_source(srcfile)
    remotedir = get_remote_dir(role) 
    # check to see if remote_dir exists
    test_remote_dir(remotedir)
    dest = get_dest(remotedir, srcfile, role) 
    result = copy_file_to_server(source, dest)
    return result

def deploy(roles=None):
    '''Main function to deploy software. Call this as fab deploy.'''

    # TODO implement get_roles() 

    for role in roles:
        source_files = get_srcfiles(CONFIG, role)
        # check git is up to date
        predeploy()
        @roles(role)
        resolve_dependencies(CONFIG, role)
        # copy source files
        for srcfile in source_files:
            @roles(role)
            deploy_file(srcfile, role)


# Set config
CONFIG = load_config('fab.cfg')

NETWORKCONFIG = CONFIG['network']
# allow overiding on the command line with --hosts
if not env.hosts:
    HOSTLIST = NETWORKCONFIG['hosts'].split(',')
    env.hosts = HOSTLIST

SOURCECONFIG = CONFIG['source']
# these can not be overridden
SRCDIR =  SOURCECONFIG['source_dir']
REPOSITORY = SOURCECONFIG['repository']
# this can be overridden by specifying it as an option
# to deploy e.g. fab deploy:source_files='file'
SRCFILES = SOURCECONFIG['srcfiles'].split(',')

# TODO  GET ROLES 

