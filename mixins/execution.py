__author__ = 'steven'

import subprocess, shlex

class ExecResult(object):
    def __init__(self, return_code, outs, errs, exception=None):
        self.return_code = return_code
        self.outs = outs
        self.errs = errs
        self.exception = exception


class ExecMixin(object):
    def __init__(self):
        pass

    def _safe_exec(self, command, timeout=180, cwd=None):
        if isinstance(command, str):
            command = shlex.split(command)
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
        try:
            outs, errs = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            proc.kill()
            outs, errs = proc.communicate()
            return ExecResult(proc.returncode, outs, errs, e)
        return ExecResult(proc.returncode, outs, errs)

    # Auth by key only
    def _safe_remote_exec(self, remote, command, timeout=180, cwd=None):
        if isinstance(command, str):
            command = shlex.split(command)
        if cwd:
            command.insert(0, ";")
            command.insert(0, cwd)
            command.insert(0, "cd")
        c = ["ssh", "-o", "PasswordAuthentication=no", "-o", "StrictHostKeyChecking=no", remote, " ".join(command)]
        proc = subprocess.Popen(c, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            outs, errs = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as e:
            proc.kill()
            outs, errs = proc.communicate()
            return ExecResult(proc.returncode, outs, errs, e)
        return ExecResult(proc.returncode, outs, errs)
