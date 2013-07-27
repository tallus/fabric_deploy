from fabric.api import *
from fabric.contrib.console import confirm

env.hosts = ['bruno']
word = 'Hello there'

def hello(name='world'):
    print(word + " %s!" % name)
    
def testf(tfile = 'foo'):
    with settings(warn_only=True):
        result=local("ls " +  tfile, capture=True)
    if result.failed and not confirm("Tests failed. Continue anyway?"):
        abort("Aborting at user request.")
    print('output: ' + result)

def testr(rdir='/srv/tsbackup'):
    result = run("ls " + rdir, quiet=True)
    if result.failed:
        abort("Fail!")
    else:
        print('output: ' + result)
    
