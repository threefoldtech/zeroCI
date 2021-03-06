from utils.utils import Utils

PATH = "/sandbox/code/github/threefoldtech/zeroCI/backend"
TIMEOUT = 5


class Recover(Utils):
    def zeroci(self):
        cmd = f"/bin/bash -c 'cd {PATH}; python3 zeroci.py &>> zeroci.log &'"
        self.execute_cmd(cmd, timeout=TIMEOUT)

    def redis(self):
        cmd = "redis-server /etc/redis/redis.conf"
        self.execute_cmd(cmd=cmd, timeout=TIMEOUT)

    def worker(self, id):
        cmd = f"/bin/bash -c 'cd {PATH}; python3 worker{id}.py &>> worker_{id}.log &'"
        self.execute_cmd(cmd=cmd, timeout=TIMEOUT)

    def scheduler(self):
        cmd = f"/bin/bash -c 'cd {PATH}; rqscheduler &>> schedule.log &'"
        self.execute_cmd(cmd=cmd, timeout=TIMEOUT)
