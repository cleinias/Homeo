/* Simple supervisor worker that responds to a few one-letter commands over a TCP/IP connection
 * Default port is 10021
 *
 * Accepted commmands and corresponding webots functions (if any) are:
 * R - Reset the Simulation to initial conditions           --> simulationRevert()
 * P - Reset the Simulation's physics to initial conditions --> simulationResetPhysics()
 * Q - Quit Webots                                          --> simulationQuit(int status);
 * D - Return distance between robot and target
 * M - Set robot's model field to a string
*/


#include "robotworker.h"
#include <webots/Supervisor.hpp>
#include <QtCore/QCoreApplication>
#include <QtCore/QThread>
#include <QtCore/QDebug>

#include <math.h>

using namespace std;
using namespace webots;

static const int TIME_STEP = 32;

RobotWorker::RobotWorker(QObject *parent) :
    QObject(parent),
    m_targetNode(0),
    m_targetX(0.0),
    m_targetY(0.0),
    m_targetZ(0.0)
{
//    QString sensor_name = "ls%1";
//    for (int i = 0; i < NUM_SENSORS; i++) {
//        LightSensor *sensor = getLightSensor(sensor_name.arg(i).toLatin1().constData());
//        sensor->enable(TIME_STEP);
//        m_sensors.append(sensor);
//    }
    // Find list of targets
    const QString targetName = "TARGET";
    m_targetNode = getFromDef(targetName.toStdString());
    if (!m_targetNode) {
        qDebug() << "Failed to find target node from def";
    } else {
        Field* location = m_targetNode->getField("location");
        const double *pos = location->getSFVec3f();
        // qDebug() << "Position of target:" << pos[0] << pos[1] << pos[2];
        m_targetX = pos[0];
        m_targetY = pos[1];
        m_targetZ = pos[2];
    }
}

void RobotWorker::run() {
    qDebug() << "Running";
    while (step(TIME_STEP) != -1)
    {
        {
            QMutexLocker l(&m_supervisorCommandMutex);
            while(!m_supervisorCommandsQueue.isEmpty()) {
                const QString cmd = QString::fromLatin1(m_supervisorCommandsQueue.dequeue());

                if (cmd.size() == 0) {
                    qDebug() << "Got an empty command!";
                    continue;
                }

                if (cmd.at(0) == 'R') {
                    Node *robot = getFromDef("KHEPERA");
                    if (!robot) {
                        qDebug() << "Failed to find robot node";
                        continue;
                    }

                    simulationRevert();

                    emit sendCommand("r");
                } else if (cmd.at(0) == 'P') {

                    simulationPhysicsReset();

                    emit sendCommand("r");
                } else if (cmd.at(0) == 'Q') {

                    simulationQuit(EXIT_SUCCESS);

                    emit sendCommand("q");
                } else if (cmd.at(0) == 'D') {
                    Node *robot = getFromDef("KHEPERA");
                    if (!robot) {
                        qDebug() << "Failed to find robot node";
                        continue;
                    }
                    Field* translation = robot->getField("translation");
                    if (!translation) {
                        qDebug() << "Failed to find translation field of robot";
                        continue;
                    }
                    const double *pos = translation->getSFVec3f();
                    // qDebug() << "Position of robot:" << pos[0] << pos[1] << pos[2];

                    double distance = sqrt(pow(pos[0] - m_targetX, 2) + pow(pos[2] - m_targetZ, 2));
                    emit sendCommand(QString("%1").arg(distance).toLatin1());
                }  else if (cmd.at(0)== 'M'){
                    Node *robot = getFromDef("KHEPERA");
                    if (!robot) {
                        qDebug() << "Failed to find robot node";
                        continue;
                    }
                    Field *model = robot->getField("model");
                    if (!model) {
                        qDebug() << "Failed to find model field of robot";
                        continue;
                    }
                    QString mod = QString::fromStdString(model->getSFString());
                    // qDebug() << "Robot model is now: " << mod;
                    // qDebug() << "Resetting...";
                    const std::string newModelName = cmd.split(',')[1].toStdString();
                    model->setSFString(newModelName);
                    mod = QString::fromStdString(model->getSFString());
                    // qDebug() << "Robot model is now: " << mod;
                    emit sendCommand("m");
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
    QMutexLocker l(&m_supervisorCommandMutex);

    m_supervisorCommandsQueue.enqueue(command);
}
