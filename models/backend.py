from .connect import Connection
from .models import Process, Parameter


def param_json_to_obj(val, version, name=None):
    param = Parameter()
    if name:
        param.name = name
    elif "name" in val:
        param.name = val["name"]

    if version.at_least("1.0.0"):
        if "default" in val:
            param.required = False
        else:
            param.required = True
    else:
        if "required" in val:
            param.required = val["required"]

    if "schema" in val:
        param_type = ""
        if isinstance(val["schema"], list):
            param_type = []
            for schema in val["schema"]:
                if "subtype" in schema:
                    param_type.append(schema["subtype"])
                elif "type" in schema:
                    param_type.append(schema["type"])
        else:
            if "type" in val["schema"]:
                param_type = val["schema"]["type"]
        param.type = str(param_type)
        if "examples" in val["schema"]:
            param.example = val["schema"]["examples"]
    if "examples" in val:
        param.example = val["examples"][0]

    return param


def process_json_to_obj(val, version):
    process = None

    if "id" in val:
        process = Process(val["id"])
        if "parameters" in val:
            parameters = val["parameters"]
            if isinstance(parameters, dict):
                for key, p in parameters.items():
                    param = param_json_to_obj(p, version=version, name=key)
                    process.parameters.append(param)
            else:
                for p in parameters:
                    param = param_json_to_obj(p, version=version)
                    process.parameters.append(param)

        if "description" in val:
            process.desc = val["description"]

        if "returns" in val:
            process.returns = val["returns"]
            if "description" in val["returns"]:
                process.returns_desc = val["returns"]["description"]
            if "schema" in val["returns"]:
                if "subtype" in val["returns"]["schema"]:
                    process.returns = val["returns"]["schema"]["subtype"]
                elif "type" in val["returns"]["schema"]:
                    if isinstance(val["returns"]["schema"]["type"], list):
                        return_types = []
                        for rt in val["returns"]["schema"]["type"]:
                            return_types.append(rt)
                        process.returns = str(return_types)
                    else:
                        process.returns = str(val["returns"]["schema"]["type"])
    return process


class Backend:

    def __init__(self, url, username=None, password=None):

        self.url = url
        self.connection = Connection()
        if username or password:
            self.login(username, password)
        else:
            self.connection.connect(url=url)

        processes = self.connection.list_processes()

        self.processes = {}

        for p in processes:
            process = process_json_to_obj(p, self.connection.version)

            if process:
                self.processes[process.id] = process

        self.collections = self.connection.list_collections()
        self.metadata = self.connection.backend_info()
        self.jobs = self.connection.user_jobs()
        self.services = self.connection.user_services()

    def login(self, username, password=None):
        return self.connection.connect(self.url, username=username, password=password)

    def get_jobs(self):
        return self.jobs

    def get_services(self):
        return self.services

    def get_collections(self):
        return self.collections

    def get_processes(self):
        return self.processes

    def get_metadata(self):
        return self.metadata

    def get_process(self, id):
        if id in self.get_processes():
            return self.processes[id]
        else:
            return None

    def service_create(self, process):
        return self.connection.service_create(process_graph=process)

    def service_info(self, service_id):
        return self.connection.service_info(service_id=service_id)

    def service_delete(self, service_id):
        return self.connection.delete_service(service_id=service_id)

    def service_pg_info(self, service_id):
        return self.connection.pg_info_service(service_id=service_id)

    def job_create(self, process, title):
        return self.connection.job_create(process_graph=process, title=title)

    def job_start(self, job_id):
        return self.connection.job_start(job_id=job_id)

    def job_info(self, job_id):
        return self.connection.job_info(job_id=job_id)

    def job_delete(self, job_id):
        return self.connection.delete_job(job_id=job_id)

    def job_pg_info(self, job_id):
        return self.connection.pg_info_job(job_id=job_id)

    def job_result_download(self, job_id):
        return self.connection.job_result_download(job_id=job_id)