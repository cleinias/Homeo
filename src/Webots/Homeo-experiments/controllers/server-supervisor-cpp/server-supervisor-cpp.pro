INCLUDEPATH += /usr/local/webots/include/controller/cpp
LIBS = -L/usr/local/webots/lib -lController -lCppController

SOURCES = robotworker.cpp \
    sockethandler.cpp \
    server-supervisor-cpp.cpp
HEADERS = robotworker.h \
    sockethandler.h
CONFIG += qt debug

QT += network
