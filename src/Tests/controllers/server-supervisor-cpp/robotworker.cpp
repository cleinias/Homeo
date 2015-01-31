/* Simple supervisor worker that responds to a few one-letter commands over a TCP/IP connection
 * Default port is 10021
 *
 * Accepted commmands and corresponding webots supervisor functions (if any) are:
 *
 * R - Reset the simulation to initial conditions           --> simulationRevert()
 * P - Reset the simulation's physics to initial conditions --> simulationResetPhysics()
 * Q - Quit Webots                                          --> simulationQuit(int status);
 * D - Return distance between robot and target
 * M - Set robot's model field to a string
 * T - Stop the robot by setting velocity of both wheeel to 0
 * S - Set robot's starting position to given coordinates and rotation (x,y,z,xa,ya,za,a)
 *     where xa,ya,za are the coordinates of a normalized vector indicating the rotation axis
 *     and a is the angle of rotation around that axis
 *
*/


#include "robotworker.h"
#include <webots/Supervisor.hpp>
#include <QtCore/QCoreApplication>
#include <QtCore/QThread>
#include <QtCore/QtCore/QDebug>
#include <unistd.h>
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
    emitter = getEmitter("stateEmitter");

}

void RobotWorker::run() {
    qDebug() << "Running";
    QString message;
    Node *robot = getFromDef("KHEPERA");
    if (!robot) {
        qDebug() << "Failed to find robot node";
    }

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

                    simulationRevert();

                    emit sendCommand("r");
                } else if (cmd.at(0) == 'P') {

                    simulationPhysicsReset();

                    emit sendCommand("p");
                } else if (cmd.at(0) == 'Q') {

                    simulationQuit(EXIT_SUCCESS);

                    emit sendCommand("q");
                } else if (cmd.at(0) == 'D') {
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
                    Field *model = robot->getField("model");
                    if (!model) {
                        qDebug() << "Failed to find model field of robot";
                        continue;
                    }
                    message = "CLOSEFILE";                     //Close trajectory file
                    emitter->send(message.toStdString().c_str(),message.length());
                    QString mod = QString::fromStdString(model->getSFString());
                    const std::string newModelName = cmd.split(',')[1].toStdString();
                    model->setSFString(newModelName);
                    mod = QString::fromStdString(model->getSFString());

                    simulationPhysicsReset();
                    message = "NEWFILE";
                    emitter->send(message.toStdString().c_str(),message.length());

                    emit sendCommand("m");
                }  else if (cmd.at(0) =='S'){
                    Field *translation = robot->getField("translation");
                    if (!translation) {
                        qDebug() << "Failed to find translation field of robot";
                        continue;
                    }
                    Field *rotation = robot->getField("rotation");
                    if (!rotation) {
                        qDebug() << "Failed to find rotation field of robot";
                        continue;
                    }
                    message = "DONOTHING";                     //Stop recording traj
                    emitter->send(message.toStdString().c_str(),message.length());
                    message = "CLOSEFILE";                     //Close trajectory file
                    emitter->send(message.toStdString().c_str(),message.length());
                    sleep(1);                                  //Let the traj controller catch up
                    double newTranslationX = cmd.split(',')[1].toDouble();
                    double newTranslationY = cmd.split(',')[2].toDouble();
                    double newTranslationZ = cmd.split(',')[3].toDouble();
                    double newTranslation[3] = {newTranslationX, newTranslationY, newTranslationZ};
                    translation->setSFVec3f(newTranslation);

                    double newRotationX = cmd.split(',')[4].toDouble();
                    double newRotationY = cmd.split(',')[5].toDouble();
                    double newRotationZ = cmd.split(',')[6].toDouble();
                    double newRotationA = cmd.split(',')[7].toDouble();
                    double newRotation[4] = {newRotationX,newRotationY,newRotationZ,newRotationA};
                    rotation->setSFRotation(newRotation);

                    emit sendCommand("s");
                    }

                    else {
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
