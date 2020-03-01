from Jumpscale import j


class Base:
    _model = None
    _model_obj = None

    def save(self):
        self._model_obj.save()

    @property
    def id(self):
        return self._model_obj.id

    @property
    def timestamp(self):
        return self._model_obj.timestamp

    @timestamp.setter
    def timestamp(self, timestamp):
        self._model_obj.timestamp = timestamp

    @property
    def status(self):
        return self._model_obj.status

    @status.setter
    def status(self, status):
        self._model_obj.status = status

    @property
    def result(self):
        return self._model_obj.result["result"]

    @result.setter
    def result(self, result):
        self._model_obj.result["result"] = result

    @classmethod
    def distinct(cls, field, where=None):
        result = cls._model.query_model([f"distinct {field}"], whereclause=where).fetchall()
        distinct_list = []
        for i in result:
            for j in i:
                distinct_list.append(j)
        return distinct_list

    @classmethod
    def get_objects(cls, fields, where=None, order_by=None, asc=True):        
        fields_string = ", ".join([f"[{x}]" for x in fields])
        query = f"select {fields_string}, [id] FROM {cls._model.index.sql_table_name}"
        if where:
            query += f" where {where}"
        if order_by:
            order = "asc" if asc else "desc"
            query += f" order by {order_by} {order}"
        query += ";"
        values = cls._model.query(query).fetchall()
        results = []
        for value in values:
            obj = {}
            for i, field in enumerate(fields):
                obj[field] = value[i]
            obj["id"] = value[i+1]
            results.append(obj)
        return results


class RepoRun(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.repo
    timestamp** = (F)
    repo** = (S)
    branch** = (S)
    commit** = (S)
    committer** = (S)
    status** = (S)
    result = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if "id" in kwargs.keys():
            self._model_obj = self._model.find(id=kwargs["id"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.timestamp = kwargs["timestamp"]
            self._model_obj.repo = kwargs["repo"]
            self._model_obj.branch = kwargs["branch"]
            self._model_obj.commit = kwargs["commit"]
            self._model_obj.committer = kwargs["committer"]
            self._model_obj.status = kwargs.get("status", "pending")
            self._model_obj.result = {"result": []}
            self._model_obj.result["result"] = kwargs.get("result", [])

    @property
    def repo(self):
        return self._model_obj.repo

    @repo.setter
    def repo(self, repo):
        self._model_obj.repo = repo

    @property
    def branch(self):
        return self._model_obj.branch

    @branch.setter
    def branch(self, branch):
        self._model_obj.branch = branch

    @property
    def commit(self):
        return self._model_obj.commit

    @commit.setter
    def commit(self, commit):
        self._model_obj.commit = commit

    @property
    def committer(self):
        return self._model_obj.committer

    @committer.setter
    def committer(self, committer):
        self._model_obj.committer = committer


class ProjectRun(Base):
    _bcdb = j.data.bcdb.get("zeroci")
    _schema_text = """@url = zeroci.project
    timestamp** = (F)
    name ** = (S)
    status** = (S)
    result = (dict)
    """
    _schema = j.data.schema.get_from_text(_schema_text)
    _model = _bcdb.model_get(schema=_schema)

    def __init__(self, **kwargs):
        if "id" in kwargs.keys():
            self._model_obj = self._model.find(id=kwargs["id"])[0]
        else:
            self._model_obj = self._model.new()
            self._model_obj.timestamp = kwargs["timestamp"]
            self._model_obj.name = kwargs["name"]
            self._model_obj.status = kwargs.get("status", "pending")
            self._model_obj.result = {"result": []}
            self._model_obj.result["result"] = kwargs.get("result", [])

    @property
    def name(self):
        return self._model_obj.name

    @name.setter
    def name(self, name):
        self._model_obj.name = name
