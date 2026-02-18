#! /usr/bin/python2
 
#===============================================================================
# Import scripts that generate python bindings for the C++ Stage library
# of the player/stage robotic simulation system.
# The script uses the pybindgen utility (https://code.google.com/p/pybindgen/)
# 
# Author: Stefano Franchi
# Date:   3/9/2015
#===============================================================================

# The following namespaces, classes, and functions are currently wrapped by the extension:
#
# Namespaces
#
# Stg
#
#
# Classes
# 
# World
# WorldGui
# Model
# 
# Functions


import pybindgen
# from pybindgen import  FileCodeSink
# from pybindgen.gccxmlparser import ModuleParser
import sys


#===============================================================================
# def stageLibModule_gen():
#     module_parser = ModuleParser('StageLib', '::')
#     module_parser.parse(["/home/stefano/builds/from-upstream-sources/stage4/Stage/libstage/stage.hh"], includes = ['"stage.hh"'], pygen_sink=FileCodeSink(sys.stdout))
#===============================================================================



def generate(file_):
    "Declare pybindgen module"
    mod = pybindgen.Module("StagePyLib")
     
    "Read Stage header file"
    mod.add_include('"/home/stefano/builds/from-upstream-sources/stage4/Stage/libstage/stage.hh"') #Notice double quotation marks
     
    "Declare Stagelib components that will be used from python"
        
    "0. NameSpaces"
    mainStageNamespace = mod.add_cpp_namespace('Stg')
    
    "1. Initialize Stage library"
    mainStageNamespace.add_function('Init', None, [('int*','argc'),
                                                   ('int*','argv[]')]) 
    
    "2. Classes and member functions"
    WorldGui = mainStageNamespace.add_class('WorldGui')
    WorldGui.add_constructor([('int', 'W'),
                                 ('int', 'H'), 
                                 ('const char*', 'L')])             # WorldGui(int W,int H,const char*L=0);
    
    # WorldGui.add_function('Load', None, [param()])            # FIX ME: ADD PARAMETERS: void WorldGui::Load(const std::string &worldfile_path)[virtual]
    # 
    # "3. Other functions"
    # 
    #  
    "Generate module"
    mod.generate(file_)
    


