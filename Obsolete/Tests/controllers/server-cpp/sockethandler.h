#ifndef SOCKETHANDLER_H
#define SOCKETHANDLER_H

#include <QtCore/QObject>
#include <QtNetwork/QAbstractSocket>

class QTcpServer;
class QTcpSocket;

class SocketHandler : public QObject
{
    Q_OBJECT
public:
    explicit SocketHandler(int port, QObject *parent = 0);

signals:
    void clientCommand(const QByteArray &cmd);

public slots:
    void newConnection();
    void clientReadyRead();
    void clientDisconnected();
    void clientError(QAbstractSocket::SocketError error);

    void sendCommand(const QByteArray &cmd);

private:
    QTcpServer *m_server;
    QTcpSocket *m_client;

};

#endif // SOCKETHANDLER_H
