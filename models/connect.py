import requests
import json
from distutils.version import LooseVersion
from requests.auth import HTTPBasicAuth
from typing import Union
import os
import sys


class Connection:

    def __init__(self):
        self.token = None
        self._url = None
        self.version = None
        self.username = None
        self.password = None

    def connect(self, url, username=None, password=None) -> bool:
        """
        Authenticates a user to the backend using auth class.
        :param url: String Backend endpoint url
        :param username: String Username credential of the user
        :param password: String Password credential of the user
        """

        self._url = url

        self.version = ComparableVersion(self.backend_info()["api_version"])

        self.token = "Undefined"
        self.username = username
        self.password = password

        if username and password:
            try:
                token = requests.get(self._url + '/credentials/basic',
                                    auth=HTTPBasicAuth(username, password), timeout=5)

                if token.status_code == 200:
                    self.token = self.parse_json_response(token)["access_token"]
                else:
                    return False

            except:
                return False
        elif username and not password:
            try:
                requests.get(self._url, timeout=5)
            except:
                return False
            return False

        if not self.token:
            return False

        return True

    def get_header(self):
        """
        Returns the header (used for a request) with e.g. the authentication token.
        :return: header: Dict
        """
        if self.token:
            return {'Authorization': 'Bearer basic//{}'.format(self.token)}
        else:
            return {}

    def get_auth(self):
        """
        Returns the authentication type (used for a request).
        :return: auth type: Dict
        """
        return None

    def list_processes(self) -> dict:
        """
        Loads all available processes of the back end.
        :return: processes_dict: Dict All available processes of the back end.
        """
        processes = self.get('/processes', auth=False)

        if processes:
            response = self.parse_json_response(processes)

            if "processes" in response:
                return response["processes"]

        return []

    def list_collections(self) -> dict:
        """
        Loads all available imagecollections types.
        :return: data_dict: Dict All available data types
        """
        data = self.get('/collections', auth=False)

        if data:
            response = self.parse_json_response(data)

            if "collections" in response:
                return response["collections"]

        return []

    def get_collection(self, collection_id) -> dict:
        """
        Loads all available imagecollections types.
        :return: data_dict: Dict All available data types
        """
        data = self.get('/collections/{}'.format(collection_id), auth=False)

        response = None

        if data.status_code == 200:
            response = self.parse_json_response(data)

        return response

    def backend_info(self) -> dict:
        """
        Loads all available imagecollections types.
        :return: data_dict: Dict All available data types
        """
        data = self.get('/', auth=False)

        response = None

        if data:
            response = self.parse_json_response(data)

        return response

    def user_jobs(self) -> dict:
        """
        Loads all jobs of the current user.
        :return: jobs: Dict All jobs of the user
        """
        jobs = self.get('/jobs', auth=True)

        if jobs.status_code > 299:
            return None

        # print("Job response status: {}".format(jobs.status_code))
        if jobs:
            jobs = self.parse_json_response(jobs)

            if "jobs" in jobs:
                jobs = jobs["jobs"]
            return jobs

        return []

    def user_services(self) -> dict:
        """
        Loads all jobs of the current user.
        :return: jobs: Dict All jobs of the user
        """
        services = self.get('/services', auth=True)

        if services:
            services = self.parse_json_response(services)

            if "services" in services:
                services = services["services"]
            return services

        return services

    def user_service(self, id) -> dict:
        """
        Loads all jobs of the current user.
        :return: jobs: Dict All jobs of the user
        """
        service = self.get('/services/{}'.format(id), auth=True)

        if service:
            service = self.parse_json_response(service)

            return service

        return service

    def job_start(self, job_id):
        """
        Starts the execution of a job at the backend.
        :param: job_id: Identifier of the job
        :return: jobs: Dict All jobs of the user
        """
        resp = self.post("/jobs/{}/results".format(job_id), postdata=None)
        return resp

    def job_cancel(self, job_id):
        """
        Cancels the execution of a job at the backend.
        :param: job_id: Identifier of the job
        """
        resp = self.delete("/jobs/{}/results".format(job_id))
        return resp

    def job_info(self, job_id):
        """
        Returns information about a created job.
        :param: job_id: Identifier of the job
        :return: job_info_id: Strings containing details about the created jobs.
        """
        requested_info = "/jobs/{}".format(job_id)
        get_info = self.get(requested_info, stream=True)
        job_info = get_info.json()

        return job_info

    def get_file_formats(self):
        """
        Returns information about a created job.
        :param: job_id: Identifier of the job
        :return: job_info_id: Strings containing details about the created jobs.
        """
        requested_info = "/file_formats"
        get_info = self.get(requested_info, stream=True)
        return get_info.json()

    def get_service_types(self):
        requested_info = "/service_types"
        get_info = self.get(requested_info, stream=True)
        return get_info.json()

    def service_info(self, service_id):
        """
        Returns information about a created service.
        :param: service_id: Identifier of the service
        :return: service_info_id: Strings containing details about the created service.
        """
        requested_info = "/services/{}".format(service_id)
        get_info = self.get(requested_info, stream=True)
        service_info = get_info.json()


        title = service_info['title']
        description = service_info['description']
        submission = service_info['submitted']
        type = service_info['type']
        cost = service_info['costs']
        processes = []
        # Data & Extents & Processes
        for key in service_info['process_graph'].keys():
            if "load_collection" in key:
                data_set = service_info['process_graph'][key]['arguments']['id']
                temporal_extent = service_info['process_graph'][key]['arguments']['spatial_extent']
                spatial_extent = service_info['process_graph'][key]['arguments']['temporal_extent']
                processes.append(key)
                service_info_id = "Title: {}. \nDescription: {}. \nSubmission Date: {} \nType: {} \nData: {}. \nProcess(es): {}. \nSpatial Extent: {}.\nTemporal Extent: {}. \nCost: {}." \
                    .format(title, description, submission, type, data_set, processes, spatial_extent, temporal_extent, cost) \
                    .replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")
                return service_info_id

    def pg_info_job(self, job_id):
        job_info = self.job_info(job_id)
        process_graph_job = {}
        if 'process_graph' in job_info:
            process_graph_job = job_info['process_graph']
        elif "process":
            if "process_graph" in job_info["process"]:
                process_graph_job = job_info["process"]['process_graph']
        return process_graph_job

    def pg_info_service(self, service_id):
        requested_info = "/services/{}".format(service_id)
        get_info = self.get(requested_info, stream=True)
        service_info = get_info.json()
        process_graph_service = service_info['process_graph']
    #    return process_graph_service

        return service_info

    def job_result_url(self, job_id):
        """
        Get the url of the job result.
        :param: job_id: Identifier of the job
        :return: url: String, URL of the result image.
        """
        download_url = "/jobs/{}/results".format(job_id)
        r = self.get(download_url, stream=True)
        if r.status_code == 200:
            url = r.json()
            if "links" in url:
                download_url = url["links"][0]
                if "href" in download_url:
                    download_url = download_url["href"]
                    return download_url
        return None

    def job_log(self, job_id):
        """
        Downloads the log info of the job and returns it
        :param: job_id: Identifier of the job
        :return: path: String, log info
        """
        log_url = "/jobs/{}/logs".format(job_id)
        r = self.get(log_url, stream=True)

        if r.status_code == 200:
            return self.parse_json_response(r)

        return None

    def job_result(self, job_id):
        """
        Downloads the result of the job into the temporary folder.
        :param: job_id: Identifier of the job
        :return: path: String, path to the downloaded result image.
        """
        download_url = "/jobs/{}/results".format(job_id)
        r = self.get(download_url, stream=True)

        if r.status_code == 200:
            return self.parse_json_response(r)

        return None

    def download_url(self, urls, path):
        """
        Downloads the result of the URLs into a given path folder.
        :param: urls: URLs to download from
        :param: path: PATH to download to
        :return: path: String, path to the downloaded result image.
        """

        file_paths = []

        for fname, href in urls.items():
            f_path = os.path.join(path, fname)
            with open(f_path, 'wb') as handle:
                try:
                    response = requests.get(href["href"], stream=True, headers=self.get_header(), timeout=5)

                    if not response.ok:
                        print(response)

                    for block in response.iter_content(1024):

                        if not block:
                            break
                        handle.write(block)
                    file_paths.append(f_path)
                except:
                    return file_paths

        return file_paths

    def job_create(self, process_graph, title=None, desc=None):
        """
        Sends the process graph to the backend and creates a new job.
        :param: process_graph: Dict, Process Graph of the new job
        :return: status: String, Status of the job creation
        """

        batch_job = {"process": {"process_graph": process_graph}}
        if title:
            batch_job["title"] = title
        if desc:
            batch_job["description"] = desc

        #print(process_graph)
        batch_job = json.dumps(batch_job)

        job_status = self.post("/jobs", postdata=batch_job)

        if job_status.status_code != 201:
            return job_status

        return None # self.parse_json_response(job_status)

    def job_adapt(self, job_id, process_graph, title=None, desc=None):
        """
        Sends the process graph to the backend and adapts an existing job.
        :param: job_id: Int, Identifier of the exisitng job
        :param: process_graph: Dict, New Process Graph for the job
        :param: title: Str, New title for the job
        :param: desc: Str, New description for the job
        :return: status: String, Status of the job creation
        """

        batch_job = {"process": {"process_graph": process_graph}}
        if title:
            batch_job["title"] = title
        if desc:
            batch_job["description"] = desc

        #print(process_graph)
        batch_job = json.dumps(batch_job)

        job_status = self.patch("/jobs/{}".format(job_id), patchdata=batch_job)

        if job_status.status_code != 204:
             return job_status

        return None

    def service_create(self, process_graph, s_type, title="", description=""):
        """
        Sends the process graph to the backend and creates a new job.
        :param: process_graph: Dict, Process Graph of the new job
        :return: status: String, Status of the job creation
        """
        pg = {"process": {"process_graph": process_graph}, "type": s_type}

        if title:
            pg["title"] = title
        if description:
            pg["description"] = description

        service_data = json.dumps(pg)

        service_status = self.post("/services", postdata=service_data)

        return self.parse_json_response(service_status)

    def post(self, path, postdata):
        """
        Makes a RESTful POST request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :param postdata: Data of the post request
        :return: response: Response
        """

        # auth_header = self.get_header()
        # auth = self.get_auth()

        auth_header = self.get_header()
        #jsonData = json.loads(postdata)
        # {'Content-type': 'application/json', 'Accept': 'text/plain'}
        auth_header["Content-type"] = "application/json"
        auth_header["Accept"] = "text/plain"

        auth_header["User-Agent"] = "openeo-qgis-plugin/ {py}/{pv} {pl}".format(
                py=sys.implementation.name, pv=".".join(map(str, sys.version_info[:3])),
                pl=sys.platform)

        return requests.post(self._url+path, data=postdata, headers=auth_header, timeout=5)
        # return {"url": self._url+path, "json": postdata, "headers": auth_header, "returnvalue": resp}

    def delete(self, path):
        """
        Makes a RESTful DELETE request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :return: response: Response
        """
        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.delete(self._url+path, headers=auth_header, auth=auth, timeout=5)

    def delete_job(self, job_id):
        path = "/jobs/{}".format(job_id)
        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.delete(self._url+path, headers=auth_header, auth=auth, timeout=5)

    def delete_service(self, service_id):
        path = "/services/{}".format(service_id)
        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.delete(self._url+path, headers=auth_header, auth=auth, timeout=5)

    def patch(self, path, patchdata):
        """
        Makes a RESTful PATCH request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :return: response: Response
        """
        auth_header = self.get_header()
        # jsonData = json.loads(postdata)
        # {'Content-type': 'application/json', 'Accept': 'text/plain'}
        auth_header["Content-type"] = "application/json"
        auth_header["Accept"] = "text/plain"

        auth_header["User-Agent"] = "openeo-qgis-plugin/ {py}/{pv} {pl}".format(
            py=sys.implementation.name, pv=".".join(map(str, sys.version_info[:3])),
            pl=sys.platform)
        # auth = self.get_auth()
        return requests.patch(self._url+path, data=patchdata, headers=auth_header, timeout=5)

    def put(self, path, header={}, data=None):
        """
        Makes a RESTful PUT request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :param header: header that gets added to the request.
        :param data: data that gets added to the request.
        :return: response: Response
        """
        auth_header = self.get_header()
        auth = self.get_auth()

        # Merge headers
        head = auth_header.copy()
        head.update(header)

        if data:
            return requests.put(self._url+path, headers=head, data=data, auth=auth, timeout=5)
        else:
            return requests.put(self._url+path, headers=head, auth=auth, timeout=5)

    def get(self, path, stream=False, auth=True):
        """
        Makes a RESTful GET request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :param stream: True if the get request should be streamed, else False
        :param auth: True if the get request should be authenticated, else False
        :return: response: Response
        """

        if auth:
            auth_header = self.get_header()
            # auth = self.get_auth()
        else:
            auth_header = {}
            # auth = None

        try:
            resp = requests.get(self._url + path, headers=auth_header, stream=stream, timeout=5)

            if resp.status_code == 401:
                self.connect(self._url, username=self.username, password=self.password)

            return resp
        except:
            return None

    def parse_json_response(self, response: requests.Response):
        """
        Parses json response, if an error occurs it raises an Exception.
        :param response: Response of a RESTful request
        :return: response: JSON Response
        """
        if response.status_code == 200 or response.status_code == 201:
            return response.json()
        else:
            return response.json()


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
            self._version = LooseVersion(version)

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