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
     * stored in ~ .
     * Should really get the dataDir from the simulation supervisor.
     * Save file with filename equal to resulting path + an identifier
     *
     * param is either "Right" or "Left" */
    QString dirFileName = "/home/stefano/.HomeoSimDataDir.txt";
    QFile dirFile(dirFileName);
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
                        rightStrm << rightSpeed <<endl;
                    emit sendCommand("d");
                } else if (cmd.at(0) == 'L') {
                    double rightSpeed = getRightSpeed();
                    double leftSpeed = cmd.split(',')[1].toDouble();

                    setSpeed(leftSpeed, rightSpeed);
                    leftStrm << leftSpeed <<endl;
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
    rightMotorFile.close();
    leftMotorFile.close();
}


void RobotWorker::handleCommand(const QByteArray &command) {
    QMutexLocker l(&m_commandMutex);

    m_commandsQueue.enqueue(command);
}
