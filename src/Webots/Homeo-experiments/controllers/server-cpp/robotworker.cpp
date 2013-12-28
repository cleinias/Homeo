#include "robotworker.h"

#include <webots/DifferentialWheels.hpp>
#include <webots/LightSensor.hpp>

#include <QtCore/QCoreApplication>
#include <QtCore/QThread>
#include <QtCore/QDebug>

using namespace std;
using namespace webots;

static const double maxSpeed = 100.0;
static const int NUM_SENSORS = 2;
static const int TIME_STEP = 32;

RobotWorker::RobotWorker(QObject *parent) :
    QObject(parent)
{
    QString sensor_name = "ls%1";
    for (int i = 0; i < NUM_SENSORS; i++) {
        LightSensor *sensor = getLightSensor(sensor_name.arg(i).toLatin1().constData());
        sensor->enable(TIME_STEP);
        m_sensors.append(sensor);
    }
}

void RobotWorker::run() {
    qDebug() << "Running";
    while (step(TIME_STEP) != -1)
    {
        {
            QMutexLocker l(&m_commandMutex);
            while(!m_commandsQueue.isEmpty()) {
                const QString cmd = QString::fromLatin1(m_commandsQueue.dequeue());

                if (cmd.size() == 0) {
                    qDebug() << "Got an empty command!";
                    continue;
                }

                if (cmd.at(0) == 'M') {
                    double maxSpeed = getMaxSpeed();
                    const QString output = QString("m,%1").arg(maxSpeed);
                    emit sendCommand(output.toLatin1());
                } else if (cmd.at(0) == 'R') {
                    double leftSpeed = getLeftSpeed();
                    double rightSpeed = cmd.split(',')[1].toDouble();

                    setSpeed(leftSpeed, rightSpeed);

                    emit sendCommand("d");
                } else if (cmd.at(0) == 'L') {
                    double rightSpeed = getRightSpeed();
                    double leftSpeed = cmd.split(',')[1].toDouble();

                    setSpeed(leftSpeed, rightSpeed);

                    emit sendCommand("d");
                } else if (cmd.at(0) == 'O') {
                    const QString out = QString("o,%1,%2").arg(m_sensors[0]->getValue())
                                                          .arg(m_sensors[1]->getValue());
                    emit sendCommand(out.toLatin1());
                } else {
                    emit sendCommand("g");
                }
            }
        }

        QCoreApplication::processEvents(QEventLoop::ExcludeUserInputEvents | QEventLoop::ExcludeSocketNotifiers);
    }
    qDebug() << "Done stepping, got -1";
}


void RobotWorker::handleCommand(const QByteArray &command) {
    QMutexLocker l(&m_commandMutex);

    m_commandsQueue.enqueue(command);
}
