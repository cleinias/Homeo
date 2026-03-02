"""
server-supervisor-python  –  Webots R2025a supervisor controller

Python rewrite of the former C++/Qt ``server-supervisor-cpp`` controller.
Exposes a single-client TCP server whose protocol is identical to
the original so that the homeostat can control the simulation without changes.

Protocol (one command per TCP message):
    R              → worldReload(), reply "r"  (R2025a equivalent of old simulationRevert)
    P              → simulationResetPhysics(), reply "r"
    Q              → simulationQuit(0), reply "q"
    D              → reply "<distance>" (Euclidean xy between KHEPERA and TARGET)
    M,<name>       → set KHEPERA's model field to <name>, reply "m"

Port is taken from the first controllerArgs entry (default 10021).
"""

import math
import socket
import select
import sys

from controller import Supervisor

# --------------- constants ------------------------------------------------
TIME_STEP = 32          # ms


# --------------- main -----------------------------------------------------
def main():
    supervisor = Supervisor()

    # --- port from controllerArgs -----------------------------------------
    port = 10021
    args = sys.argv[1:]
    if args:
        try:
            port = int(args[0])
        except ValueError:
            pass

    # --- resolve TARGET position once at start ----------------------------
    target_node = supervisor.getFromDef("TARGET")
    target_x = target_y = 0.0
    if target_node:
        loc_field = target_node.getField("location")
        pos = loc_field.getSFVec3f()
        target_x = pos[0]
        target_y = pos[1]       # R2025a is Z-up: X,Y are horizontal
        print(f"[supervisor] TARGET at ({target_x}, {target_y})")
    else:
        print("[supervisor] WARNING: TARGET node not found")

    # --- TCP server (non-blocking) ----------------------------------------
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("0.0.0.0", port))
    srv.listen(1)
    srv.setblocking(False)
    print(f"[supervisor] listening on port {port}")

    conn = None

    # --- main loop --------------------------------------------------------
    try:
        while supervisor.step(TIME_STEP) != -1:
            # accept new connection if we don't have one
            if conn is None:
                rdy, _, _ = select.select([srv], [], [], 0)
                if rdy:
                    conn, addr = srv.accept()
                    conn.setblocking(False)
                    print(f"[supervisor] client connected from {addr}")

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
                    print("[supervisor] client disconnected")
                    conn.close()
                    conn = None
                    break

                cmd = data.decode("utf-8", errors="replace").strip()
                if not cmd:
                    continue

                first = cmd[0].upper()

                if first == "R":
                    # worldReload() is the R2025a equivalent of the
                    # old simulationRevert(): it reloads the world from
                    # disk, resetting everything including controllers.
                    conn.sendall(b"r")
                    supervisor.worldReload()

                elif first == "P":
                    supervisor.simulationResetPhysics()
                    conn.sendall(b"r")

                elif first == "Q":
                    conn.sendall(b"q")
                    supervisor.simulationQuit(0)

                elif first == "D":
                    robot_node = supervisor.getFromDef("KHEPERA")
                    if robot_node:
                        trans = robot_node.getField("translation")
                        rpos = trans.getSFVec3f()
                        dist = math.sqrt(
                            (rpos[0] - target_x) ** 2 +
                            (rpos[1] - target_y) ** 2)
                        conn.sendall(str(dist).encode())
                    else:
                        conn.sendall(b"-1")

                elif first == "M":
                    robot_node = supervisor.getFromDef("KHEPERA")
                    if robot_node:
                        model_field = robot_node.getField("model")
                        new_name = cmd.split(",", 1)[1]
                        model_field.setSFString(new_name)
                    conn.sendall(b"m")

                else:
                    conn.sendall(b"g")
    finally:
        if conn:
            conn.close()
        srv.close()


if __name__ == "__main__":
    main()
