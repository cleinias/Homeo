INCLUDEPATH += /usr/local/webots/include/controller/cpp
INCLUDEPATH += /usr/local/webots/include/qt
LIBS = -L/usr/local/webots/lib -lController -lCppController
SOURCES = robotworker.cpp \
    sockethandler.cpp \
    server-timed-cpp.cpp
HEADERS = robotworker.h \
    sockethandler.h
CONFIG += qt debug
LD_LIBRARY_PATH += /home/stefano/lib:/usr/local/webots/lib:$LD_LIBRARY_PATH
QT += network
