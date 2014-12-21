/* Simple supervisor worker that responds to a few one-letter commands over a TCP/IP connection
 * Default port is 10021
 *
 * Accepted commmands and corresponding webots functions are:
 * R - Reset the Simulation to initial conditions           --> simulationRevert()
 * P - Reset the Simulation's physics to initial conditions --> simulationResetPhysics()
 * Q - Quit Webots                                          --> simulationQuit(int status);
*/


#include "robotworker.h"
#include <webots/Supervisor.hpp>
#include <QtCore/QCoreApplication>
#include <QtCore/QThread>
#include <QtCore/QDebug>

using namespace std;
using namespace webots;

static const int TIME_STEP = 32;

RobotWorker::RobotWorker(QObject *parent) :
    QObject(parent)
{
//    QString sensor_name = "ls%1";
//    for (int i = 0; i < NUM_SENSORS; i++) {
//        LightSensor *sensor = getLightSensor(sensor_name.arg(i).toLatin1().constData());
//        sensor->enable(TIME_STEP);
//        m_sensors.append(sensor);
//    }
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

                if (cmd.at(0) == 'R') {
                    simulationRevert();
                    emit sendCommand("r");
                } else if (cmd.at(0) == 'P') {

                    simulationPhysicsReset();

                    emit sendCommand("r");
                } else if (cmd.at(0) == 'Q') {

                    simulationQuit(EXIT_SUCCESS);

                    emit sendCommand("q");
                }  else {
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
