import os
from datetime import datetime
import yaml

from utils.config import Configs
from utils.reporter import Reporter
from utils.utils import Utils
from packages.vcs.vcs import VCSFactory
from bcdb.bcdb import RepoRun, ProjectRun
from vm.vms import VMS

vms = VMS()
reporter = Reporter()
utils = Utils()


class Actions(Configs):
    _REPOS_DIR = "/opt/code/vcs_repos"

    def test_run(self, node_ip, port, id, test_script, db_run, timeout):
        """Runs tests with specific commit and store the result in DB.
        
        :param image_name: docker image tag.
        :type image_name: str
        :param id: DB id of this commit details.
        :type id: str
        """
        repo_run = db_run(id=id)
        status = "success"
        if test_script:
            for i, line in enumerate(test_script):
                status = "success"
                if line.startswith("#"):
                    continue
                response, file_path = vms.run_test(run_cmd=line, node_ip=node_ip, port=port, timeout=timeout)
                if file_path:
                    if response.returncode:
                        status = "failure"
                    try:
                        result = utils.xml_parse(path=file_path, line=line)
                        repo_run.result.append(
                            {
                                "type": "testsuite",
                                "status": status,
                                "name": result["summary"]["name"],
                                "content": result,
                            }
                        )
                    except:
                        name = "cmd {}".format(i + 1)
                        content = "stdout:\n" + response.stdout + "\nstderr:\n" + response.stderr
                        repo_run.result.append({"type": "log", "status": status, "name": name, "content": content})
                    os.remove(file_path)
                else:
                    if response.returncode:
                        status = "failure"
                    name = "cmd {}".format(i + 1)
                    content = "stdout:\n" + response.stdout + "\nstderr:\n" + response.stderr
                    repo_run.result.append({"type": "log", "status": status, "name": name, "content": content})
                repo_run.save()
        else:
            repo_run.result.append({"type": "log", "status": status, "name": "No tests", "content": "No tests found"})
            repo_run.save()

    def test_black(self, node_ip, port, id, db_run, timeout):
        """Runs black formatting test on the repo with specific commit.

        :param image_name: docker image tag.
        :type image_name: str
        :param id: DB id of this commit details.
        :type id: str
        """
        repo_run = db_run(id=id)
        link = f"{self.domain}/repos/{repo_run.repo.replace('/', '%2F')}/{repo_run.branch}/{str(repo_run.id)}"
        # link = f"{self.domain}/get_status?id={str(repo_run.id)}&n=1"
        line = "black {}/{} -l 120 -t py37 --diff --exclude 'templates'".format(self._REPOS_DIR, repo_run.repo)
        response, file = vms.run_test(run_cmd=line, node_ip=node_ip, port=port, timeout=timeout)
        if response.returncode:
            status = "failure"
        elif "reformatted" in response.stderr:
            status = "failure"
        else:
            status = "success"
        repo_run.result.append(
            {"type": "log", "status": status, "name": "Black Formatting", "content": response.stderr}
        )
        repo_run.save()

        VCSObject = VCSFactory().get_cvn(repo=repo_run.repo)
        VCSObject.status_send(status=status, link=link, commit=repo_run.commit, context="Black-Formatting")

    def build(self, install_script, id, db_run, prequisties=""):
        if install_script:
            uuid, node_ip, port = vms.deploy_vm(prequisties=prequisties)
            if uuid:
                response = vms.install_app(node_ip=node_ip, port=port, install_script=install_script)
                if response.returncode:
                    repo_run = db_run(id=id)
                    content = "stdout:\n" + response.stdout + "\nstderr:\n" + response.stderr
                    repo_run.result.append(
                        {"type": "log", "status": "error", "name": "Installation", "content": content}
                    )
                    repo_run.save()
                    self.cal_status(id=id, db_run=db_run)
                return uuid, response, node_ip, port

            else:
                repo_run = db_run(id=id)
                repo_run.result.append(
                    {"type": "log", "status": "error", "name": "Deploy", "content": "Couldn't deploy a vm"}
                )
                repo_run.save()
                self.cal_status(id=id, db_run=db_run)
        else:
            repo_run = db_run(id=id)
            repo_run.result.append(
                {"type": "log", "status": "error", "name": "ZeroCI", "content": "Didn't find something to install"}
            )
            repo_run.save()
            self.cal_status(id=id, db_run=db_run)

        return None, None, None, None

    def cal_status(self, id, db_run):
        """Calculates the status of whole tests ran on the BD's id.
        
        :param id: DB id of this commit details.
        :type id: str
        """
        repo_run = db_run(id=id)
        status = "success"
        for result in repo_run.result:
            if result["status"] != "success":
                status = result["status"]
        repo_run.status = status
        repo_run.save()

    def _install_test_scripts(self, id):
        """Read 0-CI yaml script from the repo home directory and divide it to (prequisties, install, test) scripts.

        :param id: mongo record id to get commit information.
        :type id: str
        :return: prequisties, install, test script.
        """
        repo_run = RepoRun(id=id)
        org_repo_name = repo_run.repo.split("/")[0]
        clone = """mkdir -p {repos_dir}/{org_repo_name} &&
        cd {repos_dir}/{org_repo_name} &&
        git clone {cvs_host}/{repo}.git --branch {branch} &&
        cd {repos_dir}/{repo} &&
        git reset --hard {commit} &&
        """.format(
            repos_dir=self._REPOS_DIR,
            repo=repo_run.repo,
            branch=repo_run.branch,
            commit=repo_run.commit,
            org_repo_name=org_repo_name,
            cvs_host=self.vcs_host,
        ).replace(
            "\n", " "
        )

        VCSObject = VCSFactory().get_cvn(repo=repo_run.repo)
        script = VCSObject.get_content(ref=repo_run.commit, file_path="zeroCI.yaml")
        if script:
            yaml_script = yaml.load(script)
            prequisties = yaml_script.get("prequisties")
            install = " && ".join(yaml_script.get("install"))
            install_script = clone + install
            test_script = yaml_script.get("script")
            return prequisties, install_script, test_script
        return None, None, None

    def build_and_test(self, id):
        """Builds, runs tests, calculates status and gives report on telegram and your version control system.
        
        :param id: DB id of this commit details.
        :type id: str
        """
        prequisties, install_script, test_script = self._install_test_scripts(id=id)
        uuid, response, node_ip, port = self.build(
            install_script=install_script, id=id, db_run=RepoRun, prequisties=prequisties
        )
        if uuid:
            if not response.returncode:
                self.test_black(node_ip=node_ip, port=port, id=id, db_run=RepoRun, timeout=500)
                self.test_run(node_ip=node_ip, port=port, id=id, test_script=test_script, db_run=RepoRun, timeout=3600)
                self.cal_status(id=id, db_run=RepoRun)
            vms.destroy_vm(uuid)
        reporter.report(id=id, db_run=RepoRun)

    def run_project(self, project_name, install_script, test_script, prequisties, timeout):
        status = "pending"
        project_run = ProjectRun(timestamp=datetime.now().timestamp(), status=status, name=project_name)
        project_run.save()
        id = str(project_run.id)
        uuid, response, node_ip, port = self.build(
            install_script=install_script, id=id, db_run=ProjectRun, prequisties=prequisties
        )
        if uuid:
            if not response.returncode:
                self.test_run(
                    node_ip=node_ip, port=port, id=id, test_script=test_script, db_run=ProjectRun, timeout=timeout
                )
                self.cal_status(id=id, db_run=ProjectRun)
                project_run = ProjectRun(id=id)

            vms.destroy_vm(uuid)
        link = f"{self.domain}/projects/{project_run.name.replace(' ', '%20')}/{str(project_run.id)}"
        reporter.report(id=id, db_run=ProjectRun, project_name=project_name, link=link)
