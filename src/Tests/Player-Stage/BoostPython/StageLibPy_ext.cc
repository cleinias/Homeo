/*************************************************************** 
 *Wrapper file for the boost::python generation of a Python module
 * for the Stage C++ library (from the Player/Stage robotic simulation 
 * environment.
 *
 * Author: Stefano Franchi
 * Date: 3/09/2015
 ***************************************************************/

#include <boost/python.hpp>

using namespace boost::python;

BOOST_PYTHON_MODULE(StageLibPy)
{
  class _WorldGui("WorldGui", init<int,int,const char*>())
    ;
}
