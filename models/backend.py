from .connect import Connection
from .models import Process, Service, Job
import tempfile


# def param_json_to_obj(val, version, name=None):
#     param = Parameter()
#     if name:
#         param.name = name
#     elif "name" in val:
#         param.name = val["name"]
#
#     if version.at_least("1.0.0"):
#         if "default" in val:
#             param.required = False
#         else:
#             param.required = True
#     else:
#         if "required" in val:
#             param.required = val["required"]
#
#     if "schema" in val:
#         param_type = ""
#         if isinstance(val["schema"], list):
#             param_type = []
#             for schema in val["schema"]:
#                 if "subtype" in schema:
#                     param_type.append(schema["subtype"])
#                 elif "type" in schema:
#                     param_type.append(schema["type"])
#         else:
#             if "type" in val["schema"]:
#                 param_type = val["schema"]["type"]
#         param.type = str(param_type)
#         if "examples" in val["schema"]:
#             param.example = val["schema"]["examples"]
#     if "examples" in val:
#         param.example = val["examples"][0]
#
#     return param
#
#
# def process_json_to_obj(val, version):
#     process = None
#
#     if "id" in val:
#         process = ProcessInfo(val["id"])
#         if "parameters" in val:
#             parameters = val["parameters"]
#             if isinstance(parameters, dict):
#                 for key, p in parameters.items():
#                     param = param_json_to_obj(p, version=version, name=key)
#                     process.parameters.append(param)
#             else:
#                 for p in parameters:
#                     param = param_json_to_obj(p, version=version)
#                     process.parameters.append(param)
#
#         if "description" in val:
#             process.desc = val["description"]
#
#         if "returns" in val:
#             process.returns = val["returns"]
#             if "description" in val["returns"]:
#                 process.returns_desc = val["returns"]["description"]
#             if "schema" in val["returns"]:
#                 if "subtype" in val["returns"]["schema"]:
#                     process.returns = val["returns"]["schema"]["subtype"]
#                 elif "type" in val["returns"]["schema"]:
#                     if isinstance(val["returns"]["schema"]["type"], list):
#                         return_types = []
#                         for rt in val["returns"]["schema"]["type"]:
#                             return_types.append(rt)
#                         process.returns = str(return_types)
#                     else:
#                         process.returns = str(val["returns"]["schema"]["type"])
#     return process


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
            process = Process()
            process.from_metadata(p, self.connection.version)
            # process = process_json_to_obj(p, self.connection.version)

            if process:
                self.processes[process.id] = process

        self.collections = self.connection.list_collections()
        self.metadata = self.connection.backend_info()

        self.jobs = []
        jobs = self.connection.user_jobs()
        for job_meta in jobs:
            job = Job()
            job.from_metadata(job_meta, self.connection.version)
            self.jobs.append(job)

        self.services = []
        services = self.connection.user_services()
        for serv_meta in services:
            serv = Service()
            serv.from_metadata(serv_meta, self.connection.version)
            self.services.append(serv)

    def login(self, username, password=None):
        return self.connection.connect(self.url, username=username, password=password)

    def get_jobs(self):
        self.jobs = []
        jobs = self.connection.user_jobs()
        for job_meta in jobs:
            job = Job()
            job.from_metadata(job_meta, self.connection.version)
            self.jobs.append(job)
        return self.jobs

    def get_services(self):
        self.services = []
        services = self.connection.user_services()
        for serv_meta in services:
            serv = Service()
            serv.from_metadata(serv_meta, self.connection.version)
            self.services.append(serv)
        return self.services

    def get_collections(self):
        return self.collections

    def get_bands(self, collection_id):
        bands = []

        data = self.connection.get_collection(collection_id)

        if data:
            if self.connection.version.at_least("1.0.0"):
                band_info = data['summaries']['eo:bands']
                for b in band_info:
                    bands.append(b["name"])
            else:
                bands = data['properties']['cube:dimensions']['bands']['values']

        return bands

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

    def job_create(self, process, title=None, desc=None):
        return self.connection.job_create(process_graph=process, title=title, desc=desc)

    def job_start(self, job_id):
        return self.connection.job_start(job_id=job_id)

    def job_info(self, job_id):
        return self.connection.job_info(job_id=job_id)

    def detailed_job(self, job_id):
        job_info = self.connection.job_info(job_id=job_id)
        job = Job()
        job.from_metadata(job_info, self.connection.version)
        return job

    def job_delete(self, job_id):
        return self.connection.delete_job(job_id=job_id)

    def job_pg_info(self, job_id):
        job_info = self.connection.pg_info_job(job_id=job_id)
        return job_info
        title = ""
        description = ""
        submission = ""
        cost = ""

        if "title" in job_info:
            title = job_info['title']
        if "description" in job_info:
            description = job_info['description']

        if "submitted" in job_info:
            submission = job_info['submitted']
        if "created" in job_info:
            submission = job_info['created']
        if "cost" in job_info:
            cost = job_info['costs']
        processes = []
        # Data & Extents & Processes
        if self.connection.version.at_least("1.0.0"):
            if "process" in job_info:
                for key, val in job_info['process']["process_graph"].items():
                    if val["process_id"] == "load_collection":
                        data_set = job_info['process']["process_graph"][key]['arguments']['id']
                        temporal_extent = job_info['process']["process_graph"][key]['arguments']['spatial_extent']
                        spatial_extent = job_info['process']["process_graph"][key]['arguments']['temporal_extent']
                        processes.append(key)
                        job_info_id = "Title: {}. \nDescription: {}. \nSubmission Date: {} \nData: {}. \nProcess(es): {}" \
                                      ". \nSpatial Extent: {}.\nTemporal Extent: {}. \nCost: {}." \
                            .format(title, description, submission, data_set, processes, spatial_extent, temporal_extent,
                                    cost) \
                            .replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
                        return job_info_id
            else:
                job_info_id = "Title: {}. \nDescription: {}. \nSubmission Date: {} \nCost: {}." \
                    .format(title, description, submission, cost) \
                    .replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
                return job_info_id

        else:
            for key in job_info['process_graph'].keys():
                if "load_collection" in key:
                    data_set = job_info['process_graph'][key]['arguments']['id']
                    temporal_extent = job_info['process_graph'][key]['arguments']['spatial_extent']
                    spatial_extent = job_info['process_graph'][key]['arguments']['temporal_extent']
                    processes.append(key)
                    job_info_id = "Title: {}. \nDescription: {}. \nSubmission Date: {} \nData: {}. \nProcess(es): {}" \
                                  ". \nSpatial Extent: {}.\nTemporal Extent: {}. \nCost: {}." \
                        .format(title, description, submission, data_set, processes, spatial_extent, temporal_extent,
                                cost) \
                        .replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
                    return job_info_id

    def job_result_download(self, job_id):
        req = self.connection.job_result(job_id=job_id)

        download_urls = {}

        if self.connection.version.at_least("1.0.0"):
            if "assets" in req:
                download_urls = req["assets"]
        else:
            if "links" in req:
                counter = 0
                for u in req["links"]:
                    if not "href" in u:
                        download_urls[job_id+"_"+counter] = {"href": u}
                    else:
                        download_urls[job_id + "_"+counter] = u
                    counter = counter + 1

        target = tempfile.gettempdir()

        return self.connection.download_url(download_urls, target)
