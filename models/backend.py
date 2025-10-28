#from .connect import Connection
import openeo
import threading
import io
import re
import time
import sys
import webbrowser
from .models import Process, Service, Job
import tempfile
from typing import Union
from distutils.version import LooseVersion
from packaging.version import Version
from qgis.utils import iface

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

    def __init__(self, url, username=None, password=None, oidc=False, name=False):

        self.url = url
        self.name = name
        self.connection = openeo.connect(url=url)
        self.credentials = False
        if username or password:
            self.login(username, password)
            self.credentials = True
        if oidc:
            self.login_oidc()
            self.credentials = True

        processes = self.connection.list_processes()

        self.processes = {}

        for p in processes:
            process = Process()
            process.from_metadata(p, self.get_connection_version())
            # process = process_json_to_obj(p, self.connection.version)

            if process:
                self.processes[process.id] = process

        self.collections = self.connection.list_collections()
        #it is assumed that the call to backend_info() is to get a list of availale file formats
        self.metadata = self.connection.list_file_formats()

        if self.credentials:
            self.jobs = []
            jobs = self.connection.list_jobs()
            if jobs:
                for job_meta in jobs:
                    job = Job()
                    job.from_metadata(job_meta, self.get_connection_version())
                    self.jobs.append(job)

            #TODO: get services omitted until openeo get_federation_missing is fixed
            #self.services = []
            #services = self.connection.list_services() #list services of authenticated user
            #for serv_meta in services:
            #    serv = Service()
            #    serv.from_metadata(serv_meta, self.get_connection_version())
            #    self.services.append(serv)

    def login(self, username, password=None):
        try:
            return self.connection.authenticate_basic(username=username, password=password)
        except AttributeError:
            iface.messageBar().pushMessage("Error", "login failed. connection missing")
            return self.connection
    
    def login_oidc(self):
        def run_auth(capture_buffer):
            # Redirect stdout for this thread only
            old_stdout = sys.stdout
            sys.stdout = capture_buffer
            try:
                self.connection.authenticate_oidc()
            finally:
                sys.stdout = old_stdout

        capture_buffer = io.StringIO()
        
        try:
            # open a browser window when prompted
            auth_thread = threading.Thread(target=run_auth, args=(capture_buffer,))
            auth_thread.start()

            # Monitor output buffer for URL as it appears
            url_found = None
            while auth_thread.is_alive():
                output = capture_buffer.getvalue()
                urls = re.findall(r'https?:\/\/[^\s]+', output)
                if urls:
                    url_found = urls[0]
                    break
                time.sleep(0.1)  # short wait before checking again

            if url_found:
                msg = f"Opening browser to: {url_found}"
                iface.messageBar().pushMessage(msg)
                print(msg)
                webbrowser.open(url_found)
            else:
                iface.messageBar().pushMessage("Error", "No URL found before auth finished.")
                print("No URL found before auth finished.")

            auth_thread.join()
            iface.messageBar().pushMessage("Error", "Auth process completed.")
            print("Auth process completed.")

            return self.connection.authenticate_oidc()
        except AttributeError:
            iface.messageBar().pushMessage("Error", "login failed. connection missing")
            return self.connection

    def get_jobs(self):
        self.jobs = []
        jobs = self.connection.user_jobs()

        if jobs:
            for job_meta in jobs:
                job = Job()
                job.from_metadata(job_meta, self.get_connection_version())
                self.jobs.append(job)
            return self.jobs
        return jobs

    def get_job(self, job_id):
        jobs = self.get_jobs()
        if jobs:
            for job in jobs:
                if job.id == job_id:
                    return job
        return None

    def get_services(self):
        self.services = []
        services = self.connection.list_services()
        for serv_meta in services:
            serv = Service()
            serv.from_metadata(serv_meta, self.get_connection_version())
            self.services.append(serv)
        return self.services

    def get_service(self, id):
        serv_dict = self.connection.user_service(id)
        serv = Service()
        serv.from_metadata(serv_dict, self.get_connection_version())
        return serv

    def get_collections(self):
        return self.collections

    def get_temporal_extent_col(self, collection_id):
        data = self.connection.get_collection(collection_id)

        try:
            extent = data.get("extent")
            extent = extent.get("temporal")
            extent = extent.get("interval")
            return extent
        except:
            return None

    def get_bands(self, collection_id):
        bands = []

        data = self.connection.get_collection(collection_id)

        if data:
            if self.get_connection_version().at_least("1.0.0"):
                if "eo:bands" in data['summaries']:
                    band_info = data['summaries']['eo:bands']

                    for b in band_info:
                        bands.append(b["name"])
                if "sar:bands" in data['summaries']:
                    band_info = data['summaries']['sar:bands']

                    for b in band_info:
                        bands.append(b["name"])
            else:
                bands = data['properties']['cube:dimensions']['bands']['values']

        return bands

    def get_dimensions(self, collection_id):
        dimensions = []

        if not collection_id:
            return []

        data = self.connection.get_collection(collection_id)

        if data:
            if self.get_connection_version().at_least("1.0.0"):
                if "cube:dimensions" in data:
                    for dim, _ in data["cube:dimensions"].items():
                        dimensions.append(dim)

        return dimensions

    def get_output_formats(self):
        file_formats = []

        data = self.connection.get_file_formats()

        if data:
            if "output" in data:
                for key, _ in data.get("output").items():
                    file_formats.append(key)

        return file_formats

    def get_processes(self):
        return self.processes

    def get_metadata(self):
        return self.metadata

    def get_process(self, id):
        if id in self.get_processes():
            return self.processes[id]
        else:
            return None

    def service_create(self, process, s_type, title="", description=""):
        return self.connection.service_create(process_graph=process, s_type=s_type, title=title, description=description)

    def service_info(self, service_id):
        service = self.get_service(service_id)
        title = service.title
        description = service.description
        submission = service.created
        type = service.type
        cost = service.costs
        process_graph = service.process.process_graph
        processes = []
        # Data & Extents & Processes
        service_info = "Title: {}. \nDescription: {}. \nCreation Date: {} \nType: {} \nCost: {}.\n" \
            .format(title, description, submission, type, cost)
        for key, val in process_graph.items():
            processes.append(key)
            if "load_collection" == val["process_id"]:
                data_set = process_graph[key]['arguments']['id']
                temporal_extent = process_graph[key]['arguments']['temporal_extent']
                spatial_extent = process_graph[key]['arguments']['spatial_extent']
                service_info += "Data: {}. \nSpatial Extent: {}.\nTemporal Extent: {}." \
                    .format(data_set, spatial_extent, temporal_extent) \
                    .replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")

        service_info += "Processes: {}".format(str(processes)).replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
        return service_info

    def service_delete(self, service_id):
        return self.connection.delete_service(service_id=service_id)

    def get_service_types(self):
        return self.connection.get_service_types()

    def service_pg_info(self, service_id):
        return self.connection.pg_info_service(service_id=service_id)

    def job_create(self, process, title=None, desc=None):
        return self.connection.job_create(process_graph=process, title=title, desc=desc)

    def job_adapt(self, job_id, process, title=None, desc=None):
        return self.connection.job_adapt(job_id=job_id, process_graph=process, title=title, desc=desc)

    def error_msg_from_resp(self, json_resp):
        # error_id = "unknown"
        error_code = "unknown"
        error_message = "unknown"
        error_url = None
        # if "id" in json_resp:
        #     error_id = json_resp["id"]
        if "code" in json_resp:
            error_code = json_resp["code"]
        if "message" in json_resp:
            error_message = json_resp["message"]
        if "url" in json_resp:
            error_url = json_resp["url"]

        msg = "{}: {}".format(error_code, error_message)

        if error_url:
            msg += "(more details: {})".format(error_url)

        if error_code == "unknown" and error_message == "unknown" and not error_url:
            return str(json_resp)

        return msg

    def job_start(self, job_id):
        job = self.connection.job(job_id)
        return job.start()

    def job_stop(self, job_id):
        job = self.connection.job(job_id)
        return job.stop()

    def job_info(self, job_id):
        job = self.connection.job(job_id)
        return job.describe()

    def detailed_job(self, job_id):
        job = Job()
        job.from_metadata(self.job_info(job_id), self.get_connection_version())
        return job

    def job_delete(self, job_id):
        job = self.connection.job(job_id)
        return job.delete()

    def job_pg_info(self, job_id):
        job_info = self.job_info(job_id)
        process_graph_job = {}
        if 'process_graph' in job_info:
            process_graph_job = job_info['process_graph']
        elif "process":
            if "process_graph" in job_info["process"]:
                process_graph_job = job_info["process"]['process_graph']
        return process_graph_job
    
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
        if self.get_connection_version().at_least("1.0.0"):
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

    def job_log(self, job_id, offset=None, level=None):
        job = self.connection.job(job_id)
        return job.logs(offset=offset, level=level)

    def job_result_download(self, job_id, directory=None):
        job = self.connection.job(job_id)
        #req = job.download_result(job_id=job_id)

        if not directory:
            target = tempfile.gettempdir()
        else:
            target = directory
        
        return job.download_result(target)

        download_urls = {}

        if self.get_connection_version().at_least("1.0.0"):
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

        if not directory:
            target = tempfile.gettempdir()
        else:
            target = directory

        return self.connection.download_url(download_urls, target)
    
    def get_connection_version(self):
        capabilities = self.connection.capabilities()
        return ComparableVersion(capabilities.api_version())
        


class ComparableVersion:
    """
    Helper to compare a version (e.g. API version) against another (threshold) version

        >>> v = ComparableVersion('1.2.3')
        >>> v.at_least('1.2.1')
        True
        >>> v.at_least('1.10.2')
        False
        >>> v > "2.0"
        False

    To express a threshold condition you sometimes want the reference value on
    the left hand side or right hand side. There are two groups of methods
    to handle each case:

    - right hand side referencing methods. These read more intuitively. For example:

        `a.at_least(b)`: a is equal or higher than b
        `a.below(b)`: a is lower than b

    - left hand side referencing methods. These allow "currying" a threshold value
      in a reusable condition callable. For example:

        `a.or_higher(b)`: b is equal or higher than a
        `a.accept_lower(b)`: b is lower than a
    """

    def __init__(self, version: Union[str, 'ComparableVersion']):
        if isinstance(version, ComparableVersion):
            self._version = version._version
        else:
            self._version = Version(version)

    def __str__(self):
        return str(self._version)

    def to_string(self):
        return str(self)

    def __ge__(self, other: Union[str, 'ComparableVersion']):
        return self._version >= ComparableVersion(other)._version

    def __gt__(self, other: Union[str, 'ComparableVersion']):
        return self._version > ComparableVersion(other)._version

    def __le__(self, other: Union[str, 'ComparableVersion']):
        return self._version <= ComparableVersion(other)._version

    def __lt__(self, other: Union[str, 'ComparableVersion']):
        return self._version < ComparableVersion(other)._version

    # Right hand side referencing expressions.
    def at_least(self, other: Union[str, 'ComparableVersion']):
        """Self is at equal or higher than other."""
        return self >= other

    def above(self, other: Union[str, 'ComparableVersion']):
        """Self is higher than other."""
        return self > other

    def at_most(self, other: Union[str, 'ComparableVersion']):
        """Self is equal or lower than other."""
        return self <= other

    def below(self, other: Union[str, 'ComparableVersion']):
        """Self is lower than other."""
        return self < other

    # Left hand side referencing expressions.
    def or_higher(self, other: Union[str, 'ComparableVersion']):
        """Other is equal or higher than self."""
        return ComparableVersion(other) >= self

    def or_lower(self, other: Union[str, 'ComparableVersion']):
        """Other is equal or lower than self"""
        return ComparableVersion(other) <= self

    def accept_lower(self, other: Union[str, 'ComparableVersion']):
        """Other is lower than self."""
        return ComparableVersion(other) < self

    def accept_higher(self, other: Union[str, 'ComparableVersion']):
        """Other is higher than self."""
        return ComparableVersion(other) > self