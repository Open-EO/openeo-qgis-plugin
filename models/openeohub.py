import requests
from distutils.version import LooseVersion
from .models import Job


def get_hub_backends():

    try:
        backendURL = requests.get('http://hub.openeo.org/api/backends', timeout=5)
    except:
        backendsALL = {}

    if backendURL.status_code == 200:
        backendsALL = backendURL.json()

    # self.processgraphEdit.setText(json.dumps(self.backendsALL, indent=4))

    backends = []

    for backend in backendsALL.values():
        if ".well-known" in str(backend):
            try:
                backend_versions = requests.get(backend, timeout=5)

                if backend_versions.status_code == 200:
                    backend_versions = backend_versions.json()
                    for versions in backend_versions.values():

                        for version in versions:
                            if "api_version" in version:
                                if LooseVersion("0.4.0") <= LooseVersion(version["api_version"]):
                                    if "url" in version:
                                        backends.append(str(version["url"]))
            except:
                print("Exception connecting to backend {}".format(backend))
        elif isinstance(backend, dict):
            for item in backend.values():
                backends.append(str(item))
        else:
            backends.append(str(backend))

    return backends
    # # Change Names from Links to Title:
    # backend_names = []
    # for index in backendsALL.items():
    #     backend_names.append(index[0])
    # # backend_names.sort(key=str.lower)


def get_hub_jobs():

    try:
        example_jobs_URL = requests.get('http://hub.openeo.org/api/process_graphs', timeout=5)
    except:
        example_jobs_URL = []

    examples_job_list = example_jobs_URL.json()

    # Get names and process graphs of all available processes (7)
    example_jobs = []

    for item in examples_job_list:
        job = Job(title=item['title'], process_graph=item['process_graph'])
        example_jobs.append(job)

    return example_jobs
