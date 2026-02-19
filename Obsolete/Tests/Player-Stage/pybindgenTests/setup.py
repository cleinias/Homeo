#!/usr/bin/env python2
from __future__ import print_function
import os
from distutils.core import setup, Extension
from stageTest import generate


os.environ["CC"] = "g++" 
os.environ["CXX"] = "g++"
try:
    os.mkdir("build")
except OSError:
    pass
module_fname = os.path.join("build", "stageLib-bindings.c")
with open(module_fname, "wt") as file_:
    print("Generating file {}".format(module_fname))
    generate(file_)

StagePyLib = Extension('StagePyLib',
                    sources = [module_fname, '/home/stefano/builds/from-upstream-sources/stage4/Stage/libstage/stage.cc'],
                    include_dirs=['.'],
                    library_dirs = ['/usr/local/lib64/'],
                    libraries = ["stage"])

setup(name='StagePyLib',
      version="0.0",
      description='Test of bindings for StageLib with pybindgen',
      author='Stefano Franchi',
      author_email='stefano.franchi@gmail.com',
      ext_modules=[StagePyLib],
     )

