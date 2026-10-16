'''
Created on Oct 14, 2026

@author: stefano

Run several experiments as concurrent subprocesses, each logging to its own
file, and show only their progress: the loop of run_direct_vehicle_ga.py
and run_phototaxis_comparison.py.
'''
import datetime
import os
import subprocess
import threading


def run_concurrently(commands, labels, log_dir, cwd, label_width=35):
    '''Run each experiment's command at once, and wait for them all.

    commands: {experiment number: argv list}; labels: {experiment number:
    a description for the closing report}.  Each experiment's whole output
    (stdout and stderr) goes to log_dir/exp<N>.log; the lines it prints
    starting with "PROGRESS:" are also shown on the console, time-stamped.
    Prints which experiments succeeded and returns {experiment number: exit
    code}.'''
    procs = {}
    for exp_num, cmd in commands.items():
        log_path = os.path.join(log_dir, 'exp%d.log' % exp_num)
        log_file = open(log_path, 'w', buffering=1)
        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            bufsize=1, text=True, cwd=cwd)
        procs[exp_num] = (proc, log_file)

    # Reader threads: save all output to log, print only PROGRESS: lines
    def reader(proc, log_file):
        for line in proc.stdout:
            line = line.rstrip('\n')
            log_file.write(line + '\n')
            if line.startswith("PROGRESS:"):
                ts = datetime.datetime.now().strftime("%H:%M:%S")
                msg = line[len("PROGRESS:"):].strip()
                print("[%s] %s" % (ts, msg), flush=True)
        proc.wait()
        log_file.close()

    threads = []
    for proc, log_file in procs.values():
        t = threading.Thread(target=reader, args=(proc, log_file), daemon=True)
        t.start()
        threads.append(t)

    # Wait for all experiments to finish
    for t in threads:
        t.join()

    # Report exit codes
    print()
    print("=" * 60)
    print("  All experiments complete")
    print("=" * 60)
    for exp_num, (proc, _) in procs.items():
        status = "OK" if proc.returncode == 0 else "FAILED (exit %d)" % proc.returncode
        print("  Exp %d %-*s %s" % (exp_num, label_width, labels[exp_num], status))
    print()
    print("  Detailed logs: %s" % os.path.abspath(log_dir))
    print("=" * 60)
    return {exp_num: proc.returncode for exp_num, (proc, _) in procs.items()}
