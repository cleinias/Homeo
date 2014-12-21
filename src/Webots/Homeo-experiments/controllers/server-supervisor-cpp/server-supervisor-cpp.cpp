/*
 * File:         slave.cpp
 * Date:         September 08
 * Description:  This controller gives to its robot the following behavior:
 *               According to the messages it receives, the robot change its
 *               behavior.
 * Author:       fabien.rohrer@cyberbotics.com
 */

#include "robotworker.h"
#include "sockethandler.h"

#include <webots/Supervisor.hpp>

#include <iostream>
#include <string>
#include <algorithm>

#include <QtCore/QCoreApplication>
#include <QtCore/QDebug>
#include <QtCore/QThread>
#include <QtCore/QStringList>

using namespace std;
using namespace webots;

int main(int argc, char** argv)
{
  QCoreApplication app(argc, argv);

  // Start up slave thread that runs forever
  RobotWorker *robot = new RobotWorker();

  QThread* thread = new QThread();
  QObject::connect(thread, SIGNAL(started()), robot, SLOT(run()));
  robot->moveToThread(thread);
  thread->start();

  // Create the socket handler that receives TCP messages
  int port = 10021;
  if (app.arguments().size() > 1) {
      port = app.arguments()[1].toInt();
  }
  SocketHandler *handler = new SocketHandler(port);

  // Connect the TCP handler to the robot worker
  QObject::connect(robot, SIGNAL(sendCommand(QByteArray)), handler, SLOT(sendCommand(QByteArray)));
  QObject::connect(handler, SIGNAL(clientCommand(QByteArray)), robot, SLOT(handleCommand(QByteArray)), Qt::QueuedConnection);

  qDebug() << "Loaded";
  return app.exec();
}
