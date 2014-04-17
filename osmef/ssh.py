import logging
log = logging.getLogger(__name__)
import os
import time
from subprocess import check_output, check_call, CalledProcessError

WORKER_FILE = "worker.c"
BUILD_SCRIPT = "build.sh"
WORKER_EXECUTABLE = "worker"
WORKER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", WORKER_FILE))
BUILDER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "resources", BUILD_SCRIPT))


def _run_remote_command(vm, command):
    command = "ssh -q -i %s %s@%s " + command
    command = command % (vm["keyfile"], vm["username"], vm["ip"])
    log.debug("Running command: %s" % command)
    command = command.split(" ")
    try:
        return check_output(command)
    except CalledProcessError:
        return None


def _check_worker_version(vm):
    command = "cat /tmp/osmef_worker_version"
    remote_ver = _run_remote_command(vm, command).split()[0]
    local_ver = check_output(["md5sum", WORKER_PATH]).split()[0]
    return remote_ver == local_ver


def _upload_worker(vm):
    command = "scp -q -i %s %s %s@%s:/tmp" % (vm["keyfile"], WORKER_PATH, vm["username"], vm["ip"])
    log.debug("Running command: %s" % command)
    check_call(command.split())
    command = "scp -q -i %s %s %s@%s:/tmp" % (vm["keyfile"], BUILDER_PATH, vm["username"], vm["ip"])
    log.debug("Running command: %s" % command)
    check_call(command.split())
    log.info("Running build script on '{}'".format(vm["name"]))
    output = _run_remote_command(vm, "bash /tmp/%s" % BUILD_SCRIPT)
    if output == "No gcc available":
        log.error("No compiler available on the virtual machine")


def start_workers(vm_setup):
    for vm in vm_setup:
        _run_remote_command(vm, "killall -q -KILL %s" % WORKER_EXECUTABLE)
        _run_remote_command(vm, "/tmp/%s" % WORKER_EXECUTABLE)


def put_workers(vm_setup):
    for vm in vm_setup:
        if not _check_worker_version(vm):
            _upload_worker(vm)
        else:
            log.info("Reusing worker on VM '%s'" % vm["name"])


def wait_boot(vm_setup):
    for vm in vm_setup:
        while True:
            ret = _run_remote_command(vm, "ls /")
            if ret is None:
                time.sleep(2)
            else:
                log.debug("VM '{}' is alive".format(vm["name"]))
                break


def get_worker_logs(vm_setup):
    cmd = "cat /tmp/osmef_worker.log"
    logs = {}
    for vm in vm_setup:
        logs[vm["name"]] = _run_remote_command(vm, cmd).decode("ASCII")
    return logs
