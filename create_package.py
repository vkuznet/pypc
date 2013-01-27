#!/usr/bin/env python
#-*- coding: ISO-8859-1 -*-
"""
File       : create_package.py
Author     : Valentin Kuznetsov <vkuznet@gmail.com>
Description: Create common structure and setup.py of python package.
"""

# system modules
import os
import sys
import time
import subprocess

from pprint import pformat
from optparse import OptionParser

if sys.version_info < (2, 6):
    raise Exception("Requires python 2.6 or greater")

class MyOptionParser: 
    "Option parser"
    def __init__(self):
        self.parser = OptionParser()
        self.parser.add_option("-p", "--package", action="store",
             type="string", default="TestPackage", dest="package",
             help="specify package name")
        self.parser.add_option("-a", "--author", action="store",
             type="string", default="Creator", dest="author",
             help="specify author name")
        self.parser.add_option("-v", "--version", action="store",
             type="string", default="development", dest="version",
             help="specify initial version name/number")

    def get_opt(self):
        "Returns parse list of options"
        return self.parser.parse_args()

class working_dir(object):
    "Context Manager for working dir"
    def __init__(self, new_dir):
        self.new_dir = new_dir
        self.orig_dir = os.getcwd()
    def __enter__(self):
        os.chdir(self.new_dir)
    def __exit__(self, exc_type, exc_val, exc_tb):
        os.chdir(self.orig_dir)

def create_dir_structure(package, author, ver):
    "Create directory structure of given package"
    if  os.path.isdir(package):
        print 'Unable to create %s, since such directory already exists' % package
        sys.exit(1)
    os.makedirs(package)
    path = os.path.join(os.getcwd(), package)
    cmd  = "sphinx-apidoc -F -H %(package)s -A '%(author)s' -V %(version)s -o sphinx %(path)s" \
            % {'package': package, 'author': author, 'version': ver, 'path': path}
    # determine if system is equipped with sphinx
    res = subprocess.Popen('type sphinx-apidoc', shell=True, stdout=subprocess.PIPE)
    sphinx = res.stdout.read().replace('\n', '').strip()
    with working_dir(package):
        for name in ['src', 'doc', 'tests', 'etc', 'bin']:
            os.makedirs(name)
        # source area
        path = 'src/python/%s' % package
        os.makedirs(path)
        with working_dir(path):
            with open('__init__.py', 'w') as init:
                doc = '__author__ = "%s"' % author
                init.write(doc)
        # tests area
        with open('tests/__init__.py', 'w') as init:
            doc = '__author__ = "%s"' % author
            init.write(doc)
        # doc area
        if  sphinx:
            print "Sphinx is detected, will generate docs"
            print cmd
            with working_dir('doc'):
                os.makedirs('sphinx')
                os.system(cmd)
    print "Created %s directory structure" % package

def help_msg():
    "Help message"
    msg = """
To build     : python setup.py build
To install   : python setup.py install --prefix=<some dir>
To clean     : python setup.py clean
To build doc : python setup.py doc
To run tests : python setup.py test
"""
    return msg

def create_test_t(package):
    "Create simple unit test example"
    doc = """#!/usr/bin/env python
#pylint: disable-msg=c0301,c0103

'''
unit test example
'''

import sys
import unittest

def fail_function(value):
    return 1./value

class testExample(unittest.TestCase):
    "A test class"
    def setUp(self):
        "set up"
        # some stuff to init for this class
        pass

    def test_equal(self):
        "Test assertEqual"
        expect = 1
        result = 1
        self.assertEqual(expect, result)

    def test_exception(self):
        "Test assertException"
        self.assertRaises(Exception, fail_function, 0)
#
# main
#
if __name__ == '__main__':
    unittest.main()
"""
    with working_dir(package):
        with working_dir('tests'):
            with open('test_t.py', 'w') as test:
                test.write(doc)

def create_setup_py(package, author, ver):
    "Create setup.py of given package"
    doc = """#!/usr/bin/env python

\"\"\"
Standard python setup.py file for %(package)s package
%(msg)s
\"\"\"
__author__ = "%(author)s"

import os
import sys
import shutil
import subprocess
from distutils.command.build_ext import build_ext
from distutils.errors import CCompilerError
from distutils.errors import DistutilsPlatformError, DistutilsExecError
from distutils.core import Extension
from unittest import TextTestRunner, TestLoader
from glob import glob
from os.path import splitext, basename, join as pjoin
from distutils.core import setup
from distutils.cmd import Command
from distutils.command.install import INSTALL_SCHEMES

# add some path which will define the version,
# e.g. it can be done in DataProvider/__init__.py
sys.path.append(os.path.join(os.getcwd(), 'src/python'))
try:
    from DataProvider import version as dp_version
except:
    dp_version = '%(version)s' # some default

required_python_version = '2.6'
if sys.platform == 'win32' and sys.version_info > (2, 6):
   # 2.6's distutils.msvc9compiler can raise an IOError when failing to
   # find the compiler
   build_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError,
                 IOError)
else:
   build_errors = (CCompilerError, DistutilsExecError, DistutilsPlatformError)

class TestCommand(Command):
    "Class to handle unit tests"
    user_options = [ ]

    def initialize_options(self):
        "Init method"
        self._dir = os.getcwd()

    def finalize_options(self):
        "Finalize method"
        pass

    def run(self):
        "Finds all the tests modules in tests/, and runs them"
        # list of files to exclude,
        # e.g. [pjoin(self._dir, 'tests', 'exclude_t.py')]
        exclude = []
        # list of test files
        testfiles = []
        for tname in glob(pjoin(self._dir, 'tests', '*_t.py')):
            if  not tname.endswith('__init__.py') and \\
                tname not in exclude:
                testfiles.append('.'.join(
                    ['tests', splitext(basename(tname))[0]])
                )
        testfiles.sort()
        try:
            tests = TestLoader().loadTestsFromNames(testfiles)
        except:
            print "Fail to load unit tests", testfiles
            raise
        test = TextTestRunner(verbosity = 2)
        test.run(tests)

class CleanCommand(Command):
    "Class which clean-up all pyc files"
    user_options = [ ]

    def initialize_options(self):
        "Init method"
        self._clean_me = [ ]
        for root, dirs, files in os.walk('.'):
            for fname in files:
                if  fname.endswith('.pyc') or fname. endswith('.py~') or \\
                    fname.endswith('.rst~'):
                    self._clean_me.append(pjoin(root, fname))
            for dname in dirs:
                if  dname == 'build':
                    self._clean_me.append(pjoin(root, dname))

    def finalize_options(self):
        "Finalize method"
        pass

    def run(self):
        "Run method"
        for clean_me in self._clean_me:
            try:
                if  os.path.isdir(clean_me):
                    shutil.rmtree(clean_me)
                else:
                    os.unlink(clean_me)
            except:
                pass

class DocCommand(Command):
    "Class which build documentation"
    user_options = [ ]

    def initialize_options(self):
        "Init method"
        pass

    def finalize_options(self):
        "Finalize method"
        pass

    def run(self):
        "Run method"
        cdir = os.getcwd()
        os.chdir(os.path.join(os.path.join(cdir, 'doc'), 'sphinx'))
        os.environ['PYTHONPATH'] = os.path.join(cdir, 'src/python')
        subprocess.call('make html', shell=True)
        os.chdir(cdir)

class BuildExtCommand(build_ext):
    "Build C-extentions"

    def initialize_options(self):
        "Init method"
        pass

    def finalize_options(self):
        "Finalize method"
        pass

    def run(self):
        "Run method"
        try:
            build_ext.run(self)
        except DistutilsPlatformError as exp:
            print exp
            print "Could not compile extension module"

    def build_extension(self, ext):
        "Build extension method"
        try:
            build_ext.build_extension(self, ext)
        except build_errors:
            print "Could not compile %%s" %% ext.name

def dirwalk(relativedir):
    "Walk a directory tree and look-up for __init__.py files"
    idir = os.path.join(os.getcwd(), relativedir)
    for fname in os.listdir(idir):
        fullpath = os.path.join(idir, fname)
        if  os.path.isdir(fullpath) and not os.path.islink(fullpath):
            for subdir in dirwalk(fullpath):  # recurse into subdir
                yield subdir
        else:
            initdir, initfile = os.path.split(fullpath)
            if  initfile == '__init__.py':
                yield initdir

def find_packages(relativedir):
    "Find list of packages in a given dir"
    packages = []
    for idir in dirwalk(relativedir):
        package = idir.replace(os.getcwd() + '/', '')
        package = package.replace(relativedir + '/', '')
        package = package.replace('/', '.')
        packages.append(package)
    return packages

def datafiles(idir, recursive=True):
    "Return list of data files in provided relative dir"
    files = []
    if  idir[0] != '/':
        idir = os.path.join(os.getcwd(), idir)
    for dirname, dirnames, filenames in os.walk(idir):
        if  dirname != idir:
            continue
        if  recursive:
            for subdirname in dirnames:
                files.append(os.path.join(dirname, subdirname))
        for filename in filenames:
            if  filename[-1] == '~':
                continue
            files.append(os.path.join(dirname, filename))
    return files

def install_prefix(idir=None):
    "Return install prefix"
    inst_prefix = sys.prefix
    for arg in sys.argv:
        if  arg.startswith('--prefix='):
            inst_prefix = os.path.expandvars(arg.replace('--prefix=', ''))
            break
    if  idir:
        return os.path.join(inst_prefix, idir)
    return inst_prefix

def main():
    "Main function"
    version      = dp_version
    name         = "%(package)s"
    description  = "%(package)s description"
    url          = "%(package)s URL"
    readme       = "%(package)s readme"
    author       = "%(author)s",
    author_email = "<%(author)s email [dot] com>",
    keywords     = ["%(package)s"]
    package_dir  = {'%(package)s': 'src/python/%(package)s'}
    packages     = find_packages('src/python')
    extentions   = [] # list your extensions here
    # Extention example
#    extentions   = [Extension('%(package)s.extensions.speed_extention',
#                    include_dirs=['extensions'],
#                    sources=['src/python/%(package)s/extensions/speed_extention.c'])]
    data_files   = [] # list of tuples whose entries are (dir, [data_files])
    data_files   = [(install_prefix('etc'), datafiles('etc')),
                    (install_prefix('bin'), datafiles('bin'))
                   ]
    cms_license  = "%(package)s license"
    classifiers  = [
        "Development Status :: 3 - Production/Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: %(package)s License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: General"
    ]

    if  sys.version < required_python_version:
        msg = "I'm sorry, but %%s %%s requires Python %%s or later."
        print msg %% (name, version, required_python_version)
        sys.exit(1)

    # set default location for "data_files" to
    # platform specific "site-packages" location
    for scheme in INSTALL_SCHEMES.values():
        scheme['data'] = scheme['purelib']

    setup(
        name                 = name,
        version              = version,
        description          = description,
        long_description     = readme,
        keywords             = keywords,
        packages             = packages,
        package_dir          = package_dir,
        data_files           = data_files,
        scripts              = datafiles('bin'),
        requires             = ['python (>=2.6)'],
        classifiers          = classifiers,
        ext_modules          = extentions,
        cmdclass             = {'build_ext': BuildExtCommand,
                                'test': TestCommand,
                                'clean': CleanCommand,
                                'doc': DocCommand},
        author               = author,
        author_email         = author_email,
        url                  = url,
        license              = cms_license,
    )

if  __name__ == "__main__":
    main()
""" % {'package': package, 'author': author, 'msg': help_msg(), 'version': ver}

    with working_dir(package):
        with open('setup.py', 'w') as setup_py:
            setup_py.write(doc)
    print "Created %s/setup.py" % package

def main():
    "Main function"
    optmgr = MyOptionParser()
    opts, _args = optmgr.get_opt()

    create_dir_structure(opts.package, opts.author, opts.version)
    create_setup_py(opts.package, opts.author, opts.version)
    create_test_t(opts.package)
    print
    print "Your package structure has been created"
    print "Package :", opts.package
    print "Author  :", opts.author
    print "Version :", opts.version
    print
    print "Here is a list of usefull commands:"
    print help_msg()

if __name__ == '__main__':
    main()


