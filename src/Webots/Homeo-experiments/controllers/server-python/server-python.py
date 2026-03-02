"""
server-python  –  Webots R2025a robot controller for Khepera II

Python rewrite of the former C++/Qt ``server-cpp`` controller.
Exposes a single-client TCP server whose protocol is identical to
the original so that the homeostat can drive the robot without changes.

Protocol (one command per TCP message):
    M           → reply "m,<maxSpeed>"
    R,<speed>   → set right-wheel velocity, reply "d"
    L,<speed>   → set left-wheel velocity, reply "d"
    O           → reply "o,<ls0>,<ls1>"

Port is taken from the first controllerArgs entry (default 10020).
"""

import os
import sys
import socket
import select
import time

from controller import Robot

# --------------- constants ------------------------------------------------
TIME_STEP = 32          # ms  (must match WorldInfo.basicTimeStep)
NUM_SENSORS = 2
MAX_SPEED = 100.0       # rad/s – same as old DifferentialWheels maxSpeed


def _data_dir():
    """Read the data directory from ~/.HomeoSimDataDir.txt (same
    convention used by the C++ controller and the trajectory supervisor).
    Creates the directory if it does not exist."""
    path = os.path.join(os.path.expanduser("~"), ".HomeoSimDataDir.txt")
    try:
        with open(path) as f:
            d = f.read().strip()
    except OSError:
        d = os.getcwd()
    os.makedirs(d, exist_ok=True)
    return d


def _log_filename(side):
    """Return full path for the motor-command CSV log file."""
    ts = time.strftime("%Y-%m-%d-%H-%M-%S")
    return os.path.join(_data_dir(),
                        f"{side}MotorCommandsWebots-{ts}.csv")


# --------------- main -----------------------------------------------------
def main():
    robot = Robot()

    # --- port from controllerArgs -----------------------------------------
    port = 10020
    args = sys.argv[1:]          # Webots passes controllerArgs here
    if args:
        try:
            port = int(args[0])
        except ValueError:
            pass

    # --- motors -----------------------------------------------------------
    left_motor  = robot.getDevice("left wheel motor")
    right_motor = robot.getDevice("right wheel motor")
    # velocity mode: position target = infinity
    left_motor.setPosition(float('inf'))
    right_motor.setPosition(float('inf'))
    left_motor.setVelocity(0.0)
    right_motor.setVelocity(0.0)

    # --- light sensors ----------------------------------------------------
    sensors = []
    for i in range(NUM_SENSORS):
        s = robot.getDevice(f"ls{i}")
        s.enable(TIME_STEP)
        sensors.append(s)

    # --- TCP server (non-blocking) ----------------------------------------
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    srv.setblocking(False)
    print(f"[server-python] listening on port {port}")

    conn = None

    # --- motor-command log files ------------------------------------------
    right_log = open(_log_filename("Right"), "w")
    left_log  = open(_log_filename("Left"),  "w")

    # --- main loop --------------------------------------------------------
    try:
        while robot.step(TIME_STEP) != -1:
            # accept new connection if we don't have one
            if conn is None:
                rdy, _, _ = select.select([srv], [], [], 0)
                if rdy:
                    conn, addr = srv.accept()
                    conn.setblocking(False)
                    print(f"[server-python] client connected from {addr}")

            if conn is None:
                continue

            # read all available commands
            while True:
                rdy, _, _ = select.select([conn], [], [], 0)
                if not rdy:
                    break
                try:
                    data = conn.recv(1024)
                except ConnectionError:
                    data = b""
                if not data:
                    # client disconnected
                    print("[server-python] client disconnected")
                    conn.close()
                    conn = None
                    break

                cmd = data.decode("utf-8", errors="replace").strip()
                if not cmd:
                    continue

                first = cmd[0].upper()

                if first == "M":
                    reply = f"m,{MAX_SPEED}"
                    conn.sendall(reply.encode())

                elif first == "R":
                    speed = float(cmd.split(",")[1])
                    right_motor.setVelocity(speed)
                    right_log.write(f"{speed}\n")
                    right_log.flush()
                    conn.sendall(b"d")

                elif first == "L":
                    speed = float(cmd.split(",")[1])
                    left_motor.setVelocity(speed)
                    left_log.write(f"{speed}\n")
                    left_log.flush()
                    conn.sendall(b"d")

                elif first == "O":
                    v0 = sensors[0].getValue()
                    v1 = sensors[1].getValue()
                    reply = f"o,{v0},{v1}"
                    conn.sendall(reply.encode())

                else:
                    conn.sendall(b"g")
    finally:
        right_log.close()
        left_log.close()
        if conn:
            conn.close()
        srv.close()


if __name__ == "__main__":
    main()
