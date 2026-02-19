/* Simple TCP/IP slave that execute commands according to the following protocol:
 *
 * All commands are comma-separated strings with **FOUR*  mandatory fields: command name, parameter, cmd number, time.
 * Parameter and cmdNNo field may be empty. The time argument is mandatory and indicates when  the command should be executed
 * (indicated in Webots' time).
 * If the command time < 0 the command may be executed at any (Webots') time
 * Currently recognized commands are:
 *
 * L,  speed, time, cmdNo : Change speed of left motor to speed
 * R,  speed, time, cmdNo : Change speed of right motor to speed
 * O,       , time, cmdNo : Read values of light sensors and send them to client
 * S,       , time, cmdNo : Stop robot by setting both right and left motors' speed to 0
 * Z,       , time, cmdNo : Do nothing, but report reception back to client (used to coordinate behavior between client and server)
 * T,       , time, cmdNo : Read simulation's current time and send it to the client
*/


#include "robotworker.h"

#include <webots/DifferentialWheels.hpp>
#include <webots/LightSensor.hpp>

#include <QtCore/QCoreApplication>
#include <QtCore/QThread>
#include <QtCore/QtCore/QDebug>
#include <QFile>
#include <QDateTime>
#include <QDir>

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

QString getCmdFileName(QString param){
    /* FIXME: reads dataDirectory from a file called .HomeoSimDataDir.txt
     * stored in SimsData subdirectory of parent/parent (../../SimsData) dir.
     * Should really get the dataDir from the simulation supervisor.
     * Save file with filename equal to resulting path + an identifier
     *
     * param is either "Right" or "Left" */
    QDir dir = QDir::currentPath();
    dir.cdUp();
    dir.cdUp();
    QString dirFileName = ".SimDataDir.txt";
    QFile dirFile(dir.path() + "/" + dirFileName);
    dirFile.open(QIODevice::ReadOnly);
    QTextStream inStream(&dirFile);
    QString saveDir = inStream.readLine();
    dirFile.close();
    QString timeStamp = QDateTime::currentDateTime().toString("yyyy-MM-dd-hh-mm-ss");
    QString fileName = saveDir + "/"+ param + "MotorCommandsWebots-" + timeStamp + ".csv";
    return fileName;
}

void RobotWorker::run() {
    qDebug() << "Running";
    QFile rightMotorFile(getCmdFileName("Right"));
    QFile leftMotorFile(getCmdFileName("Left"));
    rightMotorFile.open(QIODevice::WriteOnly | QIODevice::Text);
    leftMotorFile.open(QIODevice::WriteOnly | QIODevice::Text);
    QTextStream rightStrm(&rightMotorFile);
    QTextStream leftStrm(&leftMotorFile);
    double simTime;
    double exptdTime;
    QString cmdNo;
//    double queueFullTime;

    while (step(TIME_STEP) != -1)
    {simTime = getTime();
     qDebug() << "Current time is: " << simTime;
        {
            QMutexLocker l(&m_commandMutex);
            while(!m_commandsQueue.isEmpty()) {
                const QString tempCmd = QString::fromLatin1(m_commandsQueue.head());
                exptdTime = (tempCmd.split(",")[2].toDouble()) * ((double)TIME_STEP /1000);
                qDebug() << "Current time ==> "<< simTime << " -- Commands expected to be executed at ==> " << exptdTime;
                if ((exptdTime == simTime) || (exptdTime < 0)){
                    const QString cmd = QString::fromLatin1(m_commandsQueue.dequeue());
                    if (cmd.size() == 0) {
                        qDebug() << "Got an empty command!";
                        continue;
                    }
                    cmdNo = cmd.split(",")[3];
                    if (cmd.at(0) == 'M') {
                        double maxSpeed = getMaxSpeed();
                        const QString output = QString("m,%1").arg(maxSpeed);
                        emit sendCommand(output.toLatin1());
                    } else if (cmd.at(0) == 'R') {
                        double leftSpeed = getLeftSpeed();
                        double rightSpeed = cmd.split(',')[1].toDouble();

                        setSpeed(leftSpeed, rightSpeed);
                        qDebug() << "Executed command: " << cmd.at(0) << "as cmd number: " << cmdNo << "at time: " << simTime;
                        double cmdTime = getTime();
                        rightStrm << cmdNo << "," << cmdTime << ","<< exptdTime << "," << rightSpeed <<endl;
                        emit sendCommand("r");
                    } else if (cmd.at(0) == 'L') {
                        double rightSpeed = getRightSpeed();
                        double leftSpeed = cmd.split(',')[1].toDouble();

                        setSpeed(leftSpeed, rightSpeed);
                        qDebug() << "Executed command: " << cmd.at(0) << "as cmd number: " << cmdNo<< "at time: " << simTime;
                        double cmdTime = getTime();
                        leftStrm << cmdNo << "," << cmdTime << "," <<exptdTime<<"," << leftSpeed <<endl;
                        emit sendCommand("l");
                    } else if (cmd.at(0) == 'O') {
                        const QString out = QString("o,%1,%2").arg(m_sensors[0]->getValue())
                                                              .arg(m_sensors[1]->getValue());
                        emit sendCommand(out.toLatin1());
                    } else if (cmd.at(0) == 'S') {
                        setSpeed(0,0);

                        emit sendCommand("s");
                    } else if (cmd.at(0) == 'Z'){
                        double cmdTime = getTime();
                        qDebug() << "End of run at time: " << cmdTime;
                        emit sendCommand("Z");
                    } else if (cmd.at(0)=='T'){
                        double cmdTime = getTime();
                        const QString out = QString("%1").arg(cmdTime);
//                        qDebug() << "Got T. Sending " << out.toLatin1();
                        emit sendCommand(out.toLatin1());
                    }  else {
                        emit sendCommand("g");
                    }
                }
                else {
                      QObject().thread()->usleep(1000*1000*0.3);
                    qDebug() << "Wrong Time, not executing. Waiting ...";
                    break;
                }
            }
        }

        QCoreApplication::processEvents(QEventLoop::ExcludeUserInputEvents | QEventLoop::ExcludeSocketNotifiers);
    }
    qDebug() << "Done stepping, got -1";
    rightMotorFile.close();
    leftMotorFile.close();
}


void RobotWorker::handleCommand(const QByteArray &command) {
    QMutexLocker l(&m_commandMutex);

    m_commandsQueue.enqueue(command);
}
