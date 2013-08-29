# Webots Makefile system 
#
# You may add some variable definitions hereafter to customize the build process
# See documentation in $(WEBOTS_HOME_PATH)/resources/Makefile.include


ifeq ($(OS),Windows_NT)
# on Windows, need to link with WinSock2
LIBRARIES=-lws2_32
endif

EXTRA_TARGETS=clients

### Do not modify: this includes Webots global Makefile.include
space :=
space +=
WEBOTS_HOME_PATH=$(subst $(space),\ ,$(strip $(subst \,/,$(WEBOTS_HOME))))
include $(WEBOTS_HOME_PATH)/resources/Makefile.include

clients:
	$(MAKE) -f Makefile.client $(MAKECMDGOALS)
