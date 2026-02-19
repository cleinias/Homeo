#ifndef ROBOTTHREAD_H
#define ROBOTTHREAD_H

#include <webots/DifferentialWheels.hpp>

#include <QtCore/QObject>
#include <QtCore/QQueue>
#include <QtCore/QMutex>

namespace webots {
    class LightSensor;
}

class RobotWorker : public QObject, public webots::DifferentialWheels
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

    QQueue<QByteArray> m_commandsQueue;
    QMutex m_commandMutex;
};

#endif // ROBOTTHREAD_H
