#!/usr/bin/env python
USAGE = """\
usage: py2dsc [options] distfile
   or: py2dsc --help

where distfile is a .zip or .tar.gz file built with the sdist command
of distutils.
"""

import sys, os, shutil, subprocess
from distutils.util import strtobool
from distutils.fancy_getopt import FancyGetopt, translate_longopt
from stdeb.util import DebianInfo, stdeb_cmdline_opts, stdeb_cmd_bool_opts
from stdeb.util import expand_tarball, expand_zip

class OptObj: pass

def runit():
    # process command-line options
    bool_opts = map(translate_longopt, stdeb_cmd_bool_opts)
    parser = FancyGetopt(stdeb_cmdline_opts+[
        ('help', 'h', "show detailed help message"),
        ])
    optobj = OptObj()
    args = parser.getopt(object=optobj)
    for option in optobj.__dict__:
        value = getattr(optobj,option)
        is_string = type(value) == str
        if option in bool_opts and is_string:
            setattr(optobj, option, strtobool(value))
            
    if hasattr(optobj,'help'):
        print USAGE
        parser.set_option_table(stdeb_cmdline_opts)
        parser.print_help("Options:")
        return 0

    if len(args)!=1:
        print 'not given single argument (distfile), args=%s'%repr(args)
        print USAGE
        return 1

    sdist_file = args[0]
    
    final_dist_dir = optobj.__dict__.get('dist_dir','deb_dist')
    tmp_dist_dir = os.path.join(final_dist_dir,'tmp_py2dsc')
    if os.path.exists(tmp_dist_dir):
        shutil.rmtree(tmp_dist_dir)
    os.makedirs(tmp_dist_dir)
        
    expand_dir = os.path.join(tmp_dist_dir,'stdeb_tmp')
    if os.path.exists(expand_dir):
        shutil.rmtree(expand_dir)
    if not os.path.exists(tmp_dist_dir):
        os.mkdir(tmp_dist_dir)
    os.mkdir(expand_dir)

    if sdist_file.lower().endswith('.zip'):
        expand_zip(os.path.abspath(sdist_file),cwd=expand_dir)
    elif sdist_file.lower().endswith('.tar.gz'):
        expand_tarball(os.path.abspath(sdist_file),cwd=expand_dir)
    else:
        raise RuntimeError('could not guess format of original sdist file')

    # now the sdist package is expanded in expand_dir
    expanded_root_files = os.listdir(expand_dir)
    assert len(expanded_root_files)==1
    repackaged_dirname = expanded_root_files[0]
    fullpath_repackaged_dirname = os.path.join(tmp_dist_dir,repackaged_dirname)
    base_dir = os.path.join(expand_dir,expanded_root_files[0])
    if os.path.exists(fullpath_repackaged_dirname):
        shutil.rmtree(fullpath_repackaged_dirname)
    os.renames(base_dir, fullpath_repackaged_dirname)
    del base_dir # no longer useful

    ##############################################

    abs_dist_dir = os.path.abspath(final_dist_dir)

    extra_args = []
    for long in parser.long_opts:
        if long=='dist-dir=':
            continue # set by this invocation
        attr = parser.get_attr_name(long)[:-1]
        if hasattr(optobj,attr):
            val = getattr(optobj,attr)
            extra_args.append('--%s%s'%(long,repr(val)))

    #args = [sys.executable,'setup.py','--dist-dir=%s'%abs_dist_dir]+extra_args
    args = [sys.executable,'-c',"import stdeb, sys; f='setup.py'; sys.argv[0]=f; execfile(f)",
            'sdist_dsc','--dist-dir=%s'%abs_dist_dir,
            '--use-premade-distfile=%s'%os.path.abspath(sdist_file)]+extra_args

    print >> sys.stderr, '-='*20
    print >> sys.stderr, "running the following command in in directory: %s\n%s"%(
        fullpath_repackaged_dirname,
        ' '.join(args))
    print >> sys.stderr, '-='*20
    res = subprocess.Popen(
        args,cwd=fullpath_repackaged_dirname,
        #stdout=subprocess.PIPE,
        #stderr=subprocess.PIPE,
        )
    returncode = res.wait()
    if returncode:
        #print >> sys.stderr, 'ERROR running: %s'%(' '.join(args),)
        #print >> sys.stderr, res.stderr.read()
        return returncode
        #raise RuntimeError('returncode %d'%returncode)
    #result = res.stdout.read().strip()

    shutil.rmtree(tmp_dist_dir)
    return returncode
    
def main():
    sys.exit(runit())
    
if __name__=='__main__':
    main()
