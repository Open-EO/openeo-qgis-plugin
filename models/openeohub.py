import requests
from distutils.version import LooseVersion
from .models import HubJob

HUB_URL = "https://hub.openeo.org"


class HubBackend:

    name = None
    url = None
    version_urls = {}

    def __init__(self, url, name=None):
        self.url = url
        self.name = name
        self.version_urls = self.fetch_version_urls()

    def get_latest_version(self):
        latest_ver = "0.0.0"
        for ver, _ in self.version_urls.items():
            if LooseVersion(latest_ver) <= LooseVersion(ver):
                latest_ver = ver
        return self.version_urls[latest_ver]

    def get_all_urls(self):
        return self.version_urls.values()

    def fetch_version_urls(self):
        ver_urls = {}
        try:
            backend_versions = requests.get(self.url, timeout=1)
        except:
            return ver_urls

        if backend_versions.status_code == 200:
            backend_versions = backend_versions.json()

            if "versions" in backend_versions:
                for bcknd in backend_versions["versions"]:
                    if "api_version" in bcknd:
                        try:
                            if LooseVersion("0.4.0") <= LooseVersion(bcknd["api_version"]):
                                if "url" in bcknd:
                                    ver_urls[bcknd["api_version"]] = str(bcknd["url"])
                        except:
                            continue
            elif ".well-known" in str(self.url):
                for versions in backend_versions.values():
                    for version in versions:
                        if "api_version" in version:
                            try:
                                if LooseVersion("0.4.0") <= LooseVersion(version["api_version"]):
                                    if "url" in version:
                                        ver_urls[version["api_version"]] = str(version["url"])
                            except:
                                continue
            elif isinstance(self.url, dict):
                for ver, item in self.url.items():
                    ver_urls[ver] = str(item)
            else:
                ver_urls["0.0.0"] = self.url
        return ver_urls


def get_hub_backends():

    try:
        backendURL = requests.get('{}/api/backends'.format(HUB_URL), timeout=5)
    except:
        backendsALL = {}

    if backendURL.status_code == 200:
        backendsALL = backendURL.json()
    else:
        return []
    # self.processgraphEdit.setText(json.dumps(self.backendsALL, indent=4))

    backends = []

    # Look for .well-known endpoint
    for name, url in backendsALL.items():
        backends.append(HubBackend(url, name=name))

    return backends


def get_hub_jobs():

    try:
        example_jobs_URL = requests.get('{}/api/process_graphs'.format(HUB_URL), timeout=5)
    except:
        example_jobs_URL = []

    examples_job_list = example_jobs_URL.json()

    # Get names and process graphs of all available processes (7)
    example_jobs = []

    for item in examples_job_list:
        job = HubJob(title=item['title'], process_graph=item['process_graph'])
        example_jobs.append(job)

    return example_jobs
