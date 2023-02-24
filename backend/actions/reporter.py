import json
from urllib.parse import urljoin

from models.initial_config import InitialConfig
from packages.telegram.telegram import Telegram
from packages.vcs.vcs import VCSFactory
from redis import Redis
from utils.constants import FAILURE, SUCCESS


class Reporter:
    def __init__(self):
        self._redis = None
        self._telegram = None
        self._vcs = None

    @property
    def redis(self):
        if not self._redis:
            self._redis = Redis()
        return self._redis

    @property
    def telegram(self):
        if not self._telegram:
            self._telegram = Telegram()
        return self._telegram

    @property
    def vcs(self):
        if not self._vcs:
            self._vcs = VCSFactory().get_cvn()
        return self._vcs

    def report(self, run_id, run_obj):
        """Report the result to the commit status and Telegram chat.

        :param run_id: DB's run_id of this run details.
        :type run_id: str
        :param parent_model: the class that the passed id is belonging to.
        :type parent_model: class
        :param schedule_name: it will have a value if the run is scheduled.
        :param schedule_name: str
        """
        configs = InitialConfig()
        bin_release = run_obj.bin_release
        triggered_by = run_obj.triggered_by
        msg = self.report_msg(status=run_obj.status)
        url = f"/repos/{run_obj.repo}/{run_obj.branch}/{run_obj.run_id}"
        link = urljoin(configs.domain, url)
        if bin_release:
            bin_url = f"/bin/{run_obj.repo}/{run_obj.branch}/{bin_release}"
            bin_link = urljoin(configs.domain, bin_url)
        else:
            bin_link = None
        data = {
            "timestamp": run_obj.timestamp,
            "commit": run_obj.commit,
            "committer": run_obj.committer,
            "status": run_obj.status,
            "repo": run_obj.repo,
            "branch": run_obj.branch,
            "bin_release": bin_release,
            "triggered_by": triggered_by,
            "run_id": run_id,
        }
        self.redis.publish("zeroci_status", json.dumps(data))
        self.vcs._set_repo_obj(repo=run_obj.repo)
        self.vcs.status_send(status=run_obj.status, link=link, commit=run_obj.commit)
        self.telegram.send_msg(
            msg=msg,
            link=link,
            repo=run_obj.repo,
            branch=run_obj.branch,
            commit=run_obj.commit,
            committer=run_obj.committer,
            bin_link=bin_link,
            triggered_by=triggered_by,
        )

    def report_msg(self, status):
        if status == SUCCESS:
            msg = f"✅ Run passed "
        elif status == FAILURE:
            msg = f"❌ Run failed "
        else:
            msg = f"⛔️ Run errored "

        return msg