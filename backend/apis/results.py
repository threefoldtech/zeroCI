import json

from apis.base import app, check_configs
from bottle import abort, redirect, request, static_file
from models.initial_config import InitialConfig
from models.schedule_info import ScheduleInfo
from models.scheduler_run import SchedulerRun
from models.trigger_run import TriggerRun
from packages.vcs.vcs import VCSFactory


SUCCESS = "success"
FAILURE = "failure"
ERROR = "error"
PENDING = "pending"


@app.route("/api/")
@check_configs
def home():
    """Return repos and schedules which are running on the server.
    """
    configs = InitialConfig()
    result = {"repos": [], "schedules": []}
    result["repos"] = configs.repos
    result["schedules"] = ScheduleInfo.distinct("name")
    result_json = json.dumps(result)
    return result_json


@app.route("/api/repos/<repo:path>")
@check_configs
def branch(repo):
    """Returns tests ran on this repo with specific branch or test details if id is sent.

    :param repo: repo's name
    :param branch: the branch's name in the repo
    :param id: DB id of test details.
    """
    branch = request.query.get("branch")
    id = request.query.get("id")

    if id:
        trigger_run = TriggerRun.get(id=id)
        live = True if trigger_run.status == PENDING else False
        result = json.dumps({"live": live, "result": trigger_run.result})
        return result
    if branch:
        fields = ["status", "commit", "committer", "timestamp", "bin_release", "triggered_by"]
        where = {"repo": repo, "branch": branch}
        trigger_runs = TriggerRun.get_objects(fields=fields, order_by="timestamp", asc=False, **where)
        result = json.dumps(trigger_runs)
        return result

    vcs_obj = VCSFactory().get_cvn(repo=repo)
    exist_branches = vcs_obj.get_branches()
    all_branches = TriggerRun.distinct(field="branch", repo=repo)
    deleted_branches = list(set(all_branches) - set(exist_branches))
    branches = {"exist": exist_branches, "deleted": deleted_branches}
    result = json.dumps(branches)
    return result


@app.route("/api/schedules/<schedule>")
@check_configs
def schedules(schedule):
    """Returns tests ran on this schedule or test details if id is sent.

    :param schedule: schedule's name
    :param id: DB id of test details.
    """
    id = request.query.get("id")
    if id:
        scheduler_run = SchedulerRun.get(id=id)
        live = True if scheduler_run.status == PENDING else False
        result = json.dumps({"live": live, "result": scheduler_run.result})
        return result

    fields = ["status", "timestamp", "bin_release", "triggered_by"]
    where = {"schedule_name": schedule}
    scheduler_runs = SchedulerRun.get_objects(fields=fields, order_by="timestamp", asc=False, **where)
    result = json.dumps(scheduler_runs)
    return result


@app.route("/status")
@check_configs
def status():
    """Returns repo's branch or schedule status for your version control system.
    """
    schedule = request.query.get("schedule")
    repo = request.query.get("repo")
    branch = request.query.get("branch")
    result = request.query.get("result")  # to return the run result
    fields = ["status"]
    configs = InitialConfig()
    if schedule:
        where = {"schedule_name": schedule, "status": f"{ERROR} OR {FAILURE} OR {SUCCESS}"}
        scheduler_run = SchedulerRun.get_objects(fields=fields, order_by="timestamp", asc=False, **where)
        if len(scheduler_run) == 0:
            return abort(404)

        if result:
            link = f"{configs.domain}/schedules/{schedule}?id={str(scheduler_run[0]['id'])}"
            return redirect(link)
        if scheduler_run[0]["status"] == SUCCESS:
            return static_file("svgs/build_passing.svg", mimetype="image/svg+xml", root=".")
        else:
            return static_file("svgs/build_failing.svg", mimetype="image/svg+xml", root=".")

    elif repo:
        if not branch:
            branch = "master"
        where = {"repo": repo, "branch": branch, "status": f"{ERROR} OR {FAILURE} OR {SUCCESS}"}
        trigger_run = TriggerRun.get_objects(fields=fields, order_by="timestamp", asc=False, **where)
        if len(trigger_run) == 0:
            return abort(404)
        if result:
            link = f"{configs.domain}/repos/{repo.replace('/', '%2F')}/{branch}/{str(trigger_run[0]['id'])}"
            return redirect(link)
        if trigger_run[0]["status"] == SUCCESS:
            return static_file("svgs/build_passing.svg", mimetype="image/svg+xml", root=".")
        else:
            return static_file("svgs/build_failing.svg", mimetype="image/svg+xml", root=".")

    return abort(404)
