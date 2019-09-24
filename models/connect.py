import requests
from requests.auth import HTTPBasicAuth
import tempfile
import json
import http

class Connection:
    def connect(self, url, username=None, password=None) -> bool:
        """
        Authenticates a user to the backend using auth class.
        :param url: String Backend endpoint url
        :param username: String Username credential of the user
        :param password: String Password credential of the user
        """

        self._url = url
        self.token = None
        self.username=username

        if username and password:
            token = requests.get(self._url + '/credentials/basic',
                                 auth=HTTPBasicAuth(username, password))

            if token.status_code == 200:
                self.token = token.json()["access_token"]
            else:
                return False

        # disconnect
        elif username and password == None:
            token_dis = requests.get(self._url)
            if token_dis.status_code == 200:
                return False
            else:
                return False

        return True

    def get_header(self):
        """
        Returns the header (used for a request) with e.g. the authentication token.
        :return: header: Dict
        """
        if self.token:
            return {'Authorization': 'Bearer {}'.format(self.token)}
        else:
            return {}

    def get_auth(self):
        """
        Returns the authentication type (used for a request).
        :return: auth type: Dict
        """
        return None

    def list_processes(self) -> dict:
        # TODO: Maybe format the result dictionary so that the process_id is the key of the dictionary.
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

    def user_jobs(self) -> dict:
        """
        Loads all jobs of the current user.
        :return: jobs: Dict All jobs of the user
        """
        jobs = self.get('/jobs', auth=True)

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

    def job_start(self, job_id):
        """
        Starts the execution of a job at the backend.
        :param: job_id: Identifier of the job
        :return: jobs: Dict All jobs of the user
        """
        request = self.post("/jobs/{}/results".format(job_id), postdata=None)
        return request.status_code

    def job_info(self, job_id):
        """
        Returns information about a created job.
        :param: job_id: Identifier of the job
        :return: jobs: Strings containing details about the created jobs.
        """
        requested_info = "/jobs/{}".format(job_id)
        get_info = self.get(requested_info, stream=True)
        job_info = json.loads(get_info)

        #title = job_info['title']
        #description = job_info['description']
        #process_graph = job_info['process_graph']
        #cost = job_info['costs']
        #processes = []
        # Data & Extents & Processes
        for key in job_info['process_graph'].keys():
            if "load_collection" in key:
                data_set = job_info['process_graph'][key]['arguments']['id']
                temporal_extent = job_info['process_graph'][key]['arguments']['spatial_extent']
                spatial_extent = job_info['process_graph'][key]['arguments']['temporal_extent']
                processes.append(key)

                #job_info_id = "Title: {}. \nDescription: {}. \nData: {}. \nProcess(es): {}. \nSpatial Extent: {}. \nTemporal Extent: {}. \nCost: {}.".\
                #    format(title, description, data_set, processes, spatial_extent, temporal_extent, cost).replace("'", "").replace("[", "").replace("]", "").replace("{", "").replace("}", "")

#                info_combined = "[{}], [{}]".format(job_info_id, process_graph)

 #               return info_combined

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

    def job_result_download(self, job_id):
        """
        Downloads the result of the job into the temporary folder.
        :param: job_id: Identifier of the job
        :return: path: String, path to the downloaded result image.
        """
        download_url = "/jobs/{}/results".format(job_id)
        r = self.get(download_url, stream=True)

        if r.status_code == 200:

            url = r.json()
            if "links" in url:
                download_url = url["links"][0]
                if "href" in download_url:
                    download_url = download_url["href"]

            auth_header = self.get_header()

            target = tempfile.gettempdir()+"/{}".format(job_id)

            with open(target, 'wb') as handle:
                response = requests.get(download_url, stream=True, headers=auth_header)

                if not response.ok:
                    print(response)

                for block in response.iter_content(1024):

                    if not block:
                        break
                    handle.write(block)

            return target

        return None

    def job_create(self, process_graph):
        """
        Sends the process graph to the backend and creates a new job.
        :param: process_graph: Dict, Process Graph of the new job
        :return: status: String, Status of the job creation
        """
        pg = {
            "process_graph": process_graph
        }
        #print(process_graph)

        job_status = self.post("/jobs", postdata=pg)

        #if job_status.status_code == 201:
        #    return job_status

        return job_status

    def post(self, path, postdata):
        """
        Makes a RESTful POST request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :param postdata: Data of the post request
        :return: response: Response
        """

        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.post(self._url+path, json=postdata, headers=auth_header, auth=auth)

    def delete(self, path):
        """
        Makes a RESTful DELETE request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :return: response: Response
        """
        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.delete(self._url+path, headers=auth_header, auth=auth)

    def delete_job(self, job_id):
        path = "/jobs/{}".format(job_id)
        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.delete(self._url+path, headers=auth_header, auth=auth)

    def patch(self, path):
        """
        Makes a RESTful PATCH request to the back end.
        :param path: URL of the request (without root URL e.g. "/data")
        :return: response: Response
        """
        auth_header = self.get_header()
        auth = self.get_auth()
        return requests.patch(self._url+path, headers=auth_header, auth=auth)

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
            return requests.put(self._url+path, headers=head, data=data, auth=auth)
        else:
            return requests.put(self._url+path, headers=head, auth=auth)

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
            auth = self.get_auth()
        else:
            auth_header = {}
            auth = None

        try:
            resp = requests.get(self._url + path, headers=auth_header, stream=stream, auth=auth)
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
            return None