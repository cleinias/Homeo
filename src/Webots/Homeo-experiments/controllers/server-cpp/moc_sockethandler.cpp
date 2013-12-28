/****************************************************************************
** Meta object code from reading C++ file 'sockethandler.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.2.0)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "sockethandler.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'sockethandler.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.2.0. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
struct qt_meta_stringdata_SocketHandler_t {
    QByteArrayData data[8];
    char stringdata[95];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    offsetof(qt_meta_stringdata_SocketHandler_t, stringdata) + ofs \
        - idx * sizeof(QByteArrayData) \
    )
static const qt_meta_stringdata_SocketHandler_t qt_meta_stringdata_SocketHandler = {
    {
QT_MOC_LITERAL(0, 0, 13),
QT_MOC_LITERAL(1, 14, 13),
QT_MOC_LITERAL(2, 28, 0),
QT_MOC_LITERAL(3, 29, 3),
QT_MOC_LITERAL(4, 33, 13),
QT_MOC_LITERAL(5, 47, 15),
QT_MOC_LITERAL(6, 63, 18),
QT_MOC_LITERAL(7, 82, 11)
    },
    "SocketHandler\0clientCommand\0\0cmd\0"
    "newConnection\0clientReadyRead\0"
    "clientDisconnected\0sendCommand\0"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_SocketHandler[] = {

 // content:
       7,       // revision
       0,       // classname
       0,    0, // classinfo
       5,   14, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       1,       // signalCount

 // signals: name, argc, parameters, tag, flags
       1,    1,   39,    2, 0x06,

 // slots: name, argc, parameters, tag, flags
       4,    0,   42,    2, 0x0a,
       5,    0,   43,    2, 0x0a,
       6,    0,   44,    2, 0x0a,
       7,    1,   45,    2, 0x0a,

 // signals: parameters
    QMetaType::Void, QMetaType::QByteArray,    3,

 // slots: parameters
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void,
    QMetaType::Void, QMetaType::QByteArray,    3,

       0        // eod
};

void SocketHandler::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        SocketHandler *_t = static_cast<SocketHandler *>(_o);
        switch (_id) {
        case 0: _t->clientCommand((*reinterpret_cast< const QByteArray(*)>(_a[1]))); break;
        case 1: _t->newConnection(); break;
        case 2: _t->clientReadyRead(); break;
        case 3: _t->clientDisconnected(); break;
        case 4: _t->sendCommand((*reinterpret_cast< const QByteArray(*)>(_a[1]))); break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (SocketHandler::*_t)(const QByteArray & );
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&SocketHandler::clientCommand)) {
                *result = 0;
            }
        }
    }
}

const QMetaObject SocketHandler::staticMetaObject = {
    { &QObject::staticMetaObject, qt_meta_stringdata_SocketHandler.data,
      qt_meta_data_SocketHandler,  qt_static_metacall, 0, 0}
};


const QMetaObject *SocketHandler::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *SocketHandler::qt_metacast(const char *_clname)
{
    if (!_clname) return 0;
    if (!strcmp(_clname, qt_meta_stringdata_SocketHandler.stringdata))
        return static_cast<void*>(const_cast< SocketHandler*>(this));
    return QObject::qt_metacast(_clname);
}

int SocketHandler::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QObject::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 5)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 5;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 5)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 5;
    }
    return _id;
}

// SIGNAL 0
void SocketHandler::clientCommand(const QByteArray & _t1)
{
    void *_a[] = { 0, const_cast<void*>(reinterpret_cast<const void*>(&_t1)) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}
QT_END_MOC_NAMESPACE
