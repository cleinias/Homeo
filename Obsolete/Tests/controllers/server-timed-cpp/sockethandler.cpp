#include "sockethandler.h"

#include <QtNetwork/QTcpSocket>
#include <QtNetwork/QTcpServer>

SocketHandler::SocketHandler(int port, QObject *parent) :
    QObject(parent),
    m_client(0)
{
    m_server = new QTcpServer(this);

    connect(m_server, SIGNAL(newConnection()), this, SLOT(newConnection()));

    m_server->listen(QHostAddress::Any, port);
}

void SocketHandler::newConnection() {
    QTcpSocket *socket = m_server->nextPendingConnection();

    connect(socket, SIGNAL(disconnected()), this, SLOT(clientDisconnected()));
    qDebug() << "Got a connection";

    if (m_client != 0) {
        qDebug() << "HELP! Already have a client but I have a new connection";
        return;
    }

    m_client = socket;

    connect(m_client, SIGNAL(readyRead()), this, SLOT(clientReadyRead()));
    connect(m_client, SIGNAL(error(QAbstractSocket::SocketError)), this, SLOT(clientError(QAbstractSocket::SocketError)));
}

void SocketHandler::clientReadyRead() {
    if (m_client->bytesAvailable() == 0) {
        qDebug() << "Ready but no bytes available";
        return;
    }

    QByteArray data = m_client->readAll();
    qDebug() << "Robot server read:" << data;
    emit clientCommand(data);
}

void SocketHandler::sendCommand(const QByteArray &cmd) {
    if (m_client == 0) {
        qDebug() << "Can't send a command without a connected client!";
        return;
    }

    //qDebug() << "Sending reply:" << cmd;
    m_client->write(cmd);
    m_client->flush();
}

void SocketHandler::clientDisconnected() {
    QTcpSocket *client = qobject_cast<QTcpSocket *>(sender());

    if (m_client != client) {
        qDebug() << "Got a disconnected event for a socket that is NOT m_client?!";
    }

    qDebug() << "Lost client";

    m_client = 0;

    client->deleteLater();
}

void SocketHandler::clientError(QAbstractSocket::SocketError error) {
    qDebug() << "Got socket error from connected client:" << error;
}
