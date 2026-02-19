#ifndef ROBOTTHREAD_H
#define ROBOTTHREAD_H

#include <webots/Supervisor.hpp>
#include <webots/Node.hpp>

#include <QtCore/QObject>
#include <QtCore/QQueue>
#include <QtCore/QMutex>

namespace webots {
    class LightSensor;
}

class RobotWorker : public QObject, public webots::Supervisor
{
    Q_OBJECT
public:
    explicit RobotWorker(QObject *parent = 0);

signals:
    void sendCommand(const QByteArray& command);

public slots:
    void run();
    void handleCommand(const QByteArray& command);

private:
    QList<webots::LightSensor*> m_sensors;

    webots::Node* m_targetNode;
    double m_targetX, m_targetY, m_targetZ;
    webots::Emitter* emitter;

    QQueue<QByteArray> m_supervisorCommandsQueue;
    QMutex m_supervisorCommandMutex;
};

#endif // ROBOTTHREAD_H
