INCLUDEPATH = /usr/local/webots/include/controller/cpp
LIBS = -L/usr/local/webots/lib -lController -lCppController

SOURCES = server-cpp.cpp robotworker.cpp \
    sockethandler.cpp
HEADERS = robotworker.h \
    sockethandler.h
CONFIG += qt debug

QT += network
