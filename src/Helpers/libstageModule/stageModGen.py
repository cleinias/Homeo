import pybindgen
import sys

#===============================================================================
# "A. manual operation "
# """1. Create an object to represent the module to create
#       Something like: 
#       mod = pybindgen.Module("myModule")
# 
#    2. Add the C header:
#       mod.add_include("pathname_to_header")
#       
#    3. Register the function(s) to use:
#       mod.add_function("FunctionName", returnValues, inputValues)
#            
#    4. Generate module:
#       mod.generate(sys.stdout)
#       """ 
#===============================================================================


#===============================================================================
# "B. Automatic scanning of a library header"
# 
# from pybindgen import FileCodeSink
# from pybindgen.gccxmlparser import ModuleParser
# 
# def stage_module_gen():
#     module_parser = ModuleParser('StageModule', '::')
#     module = module_parser.parse("/home/stefano/builds/from-upstream-sources/stage4/Stage/libstage/stage.hh")
#     module.add_include("stage.hh")
#     
#     pybindgen.write_preamble(FileCodeSink(sys.stdout))
#     module.generate(FileCodeSink(sys.stdout))
#     
# if __name__ == "__main__":
#     stage_module_gen()
#===============================================================================
    
    
""" Minimal set of needed functions:

1. World loading and init functions
    - Stg::Init
    - 

2. Reading sensors

3. Actuator functions

4. Simulation's management functions
    - World         Loads a world into stage 
    - Update        Runs one simulation step
    - Run           Run the world
   - 

5. Models' poses functions (moving things around, reading positions))