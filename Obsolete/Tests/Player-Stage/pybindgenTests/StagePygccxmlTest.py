#! /usr/bin/python2
import pybindgen
from pybindgen import  FileCodeSink
from pybindgen.gccxmlparser import ModuleParser
import sys


def stageLibModule_gen():
    module_parser = ModuleParser('StageLib', '::')
    module_parser.parse(["/home/stefano/builds/from-upstream-sources/stage4/Stage/libstage/stage.hh"], includes = ['"stage.hh"'], pygen_sink=FileCodeSink(sys.stdout))



if __name__ == "__main__":
    stageLibModule_gen()