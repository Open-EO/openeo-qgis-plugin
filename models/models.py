from datetime import datetime
import json


def list_to_lang(list_arg):
    pretty_txt = ""

    if len(list_arg) > 0:
        pretty_txt = list_arg[0]

    for i in range(1, len(list_arg)-1):
        pretty_txt += ", {}".format(list_arg[i])

    if pretty_txt:
        pretty_txt += " or {}".format(list_arg[-1])

    return pretty_txt


class HubJob:
    title = None
    process_graph = None

    def __init__(self, title, process_graph):
        self.title = title
        self.process_graph = process_graph

    def to_job(self):
        job = Job()
        job.process = Process()
        job.process.process_graph = json.loads(self.process_graph)
        job.title = self.title
        return job


class Job:

    id = None
    title = None
    description = None
    process = None
    status = None
    progress = None
    created = None
    updated = None
    plan = None
    costs = None
    budget = None

    def __init__(self):
        pass

    def __str__(self):
        return "{} - {} - {} - {} - {} - {} - {} - {} - {} - {} - {}".format(str(self.id), str(self.title),
                                                                                       str(self.description), str(self.process),
                                                                                       str(self.status), str(self.progress),
                                                                                       str(self.created), str(self.updated),
                                                                                       str(self.plan), str(self.costs),
                                                                                       str(self.budget))

    def from_metadata(self, metadata, version):

        if version.at_least("1.0.0"):
            if "id" in metadata:
                self.id = metadata["id"]
            if "title" in metadata:
                self.title = metadata["title"]
            if "description" in metadata:
                self.description = metadata["description"]
            if "process" in metadata:
                self.process = Process()
                self.process.from_metadata(metadata["process"], version)
            if "status" in metadata:
                self.status = metadata["status"]
            if "progress" in metadata:
                self.progress = metadata["progress"]
            if "created" in metadata:
                self.created = datetime.strptime(metadata["created"], '%Y-%m-%dT%H:%M:%SZ')
            if "updated" in metadata:
                self.updated = datetime.strptime(metadata["updated"], '%Y-%m-%dT%H:%M:%SZ')
            if "plan" in metadata:
                self.plan = metadata["plan"]
            if "costs" in metadata:
                self.costs = metadata["costs"]
            if "budget" in metadata:
                self.budget = metadata["budget"]
        else:
            if "id" in metadata:
                self.id = metadata["id"]
            if "title" in metadata:
                self.title = metadata["title"]
            if "description" in metadata:
                self.description = metadata["description"]
            if "process_graph" in metadata:
                self.process = Process()
                self.process.process_graph = metadata["process_graph"]
            if "status" in metadata:
                self.status = metadata["status"]
            if "progress" in metadata:
                self.progress = metadata["progress"]
            if "submitted" in metadata:
                self.created = datetime.strptime(metadata["submitted"], '%Y-%m-%dT%H:%M:%SZ')
            if "updated" in metadata:
                self.updated = datetime.strptime(metadata["updated"], '%Y-%m-%dT%H:%M:%SZ')
            if "plan" in metadata:
                self.plan = metadata["plan"]
            if "costs" in metadata:
                self.costs = metadata["costs"]
            if "budget" in metadata:
                self.budget = metadata["budget"]


class Service:
    id = None
    title = None
    description = None
    process = None
    url = None
    type = None
    enabled = None
    configuration = None
    attributes = None
    created = None
    plan = None
    costs = None
    budget = None

    def __init__(self):
        pass

    def from_metadata(self, metadata, version):

        if not isinstance(metadata, dict):
            return

        if version.at_least("1.0.0"):
            if "id" in metadata:
                self.id = metadata["id"]
            if "title" in metadata:
                self.title = metadata["title"]
            if "description" in metadata:
                self.description = metadata["description"]
            if "process" in metadata:
                self.process = Process()
                self.process.from_metadata(metadata["process"], version)
            if "url" in metadata:
                self.url = metadata["url"]
            if "type" in metadata:
                self.type = metadata["type"]
            if "enabled" in metadata:
                self.enabled = metadata["enabled"]
            if "configuration" in metadata:
                self.configuration = metadata["configuration"]
            if "attributes" in metadata:
                self.attributes = metadata["attributes"]
            if "created" in metadata:
                self.created = datetime.strptime(metadata["created"], '%Y-%m-%dT%H:%M:%SZ')
            if "plan" in metadata:
                self.plan = metadata["plan"]
            if "costs" in metadata:
                self.costs = metadata["costs"]
            if "budget" in metadata:
                self.budget = metadata["budget"]
        else:
            if "id" in metadata:
                self.id = metadata["id"]
            if "title" in metadata:
                self.title = metadata["title"]
            if "description" in metadata:
                self.description = metadata["description"]
            if "process_graph" in metadata:
                self.process = Process()
                self.process.process_graph = metadata["process_graph"]
            if "url" in metadata:
                self.url = metadata["url"]
            if "type" in metadata:
                self.type = metadata["type"]
            if "enabled" in metadata:
                self.enabled = metadata["enabled"]
            if "parameters" in metadata:
                self.attributes = metadata["parameters"]
            if "submitted" in metadata:
                self.created = datetime.strptime(metadata["submitted"], '%Y-%m-%dT%H:%M:%SZ')
            if "plan" in metadata:
                self.plan = metadata["plan"]
            if "costs" in metadata:
                self.costs = metadata["costs"]
            if "budget" in metadata:
                self.budget = metadata["budget"]


class Process:

    id = None
    process_graph = {}
    summary = None
    description = None
    categories = []
    parameters = []
    returns = None
    deprecated = None
    experimental = None
    exceptions = None
    examples = []
    links = []

    def __init(self):
        pass

    def __str__(self):
        return str(self.id)

    def get_return_type(self):
        schema = self.returns["schema"]
        if "subtype" in schema:
            return schema["subtype"]
        elif "type" in schema:
            if isinstance(schema["type"], list):
                return list_to_lang(schema["type"])
            else:
                return schema["type"]
        elif isinstance(schema, list):
            type_list = []
            for item in schema:
                if "subtype" in item:
                    type_list.append(item["subtype"])
                elif "type" in item:
                    type_list.append(item["type"])
            return list_to_lang(type_list)
        else:
            return schema["description"]

    def from_metadata(self, metadata, version):

        if version.at_least("1.0.0"):
            if "id" in metadata:
                self.id = metadata["id"]
            if "process_graph" in metadata:
                self.process_graph = metadata["process_graph"]
            if "summary" in metadata:
                self.summary = metadata["summary"]
            if "description" in metadata:
                self.description = metadata["description"]
            if "categories" in metadata:
                self.categories = metadata["categories"]
            if "parameters" in metadata:
                self.parameters = []
                for metap in metadata["parameters"]:
                    param = Parameter()
                    param.from_metadata(metap, version)
                    self.parameters.append(param)
            if "returns" in metadata:
                self.returns = metadata["returns"]
            if "deprecated" in metadata:
                self.deprecated = metadata["deprecated"]
            if "experimental" in metadata:
                self.experimental = metadata["experimental"]
            if "exceptions" in metadata:
                self.exceptions = metadata["exceptions"]
            if "examples" in metadata:
                self.examples = metadata["examples"]
            if "links" in metadata:
                self.links = metadata["links"]
        else:
            if "processes" in metadata:
                metadata = metadata["processes"]
                if "id" in metadata:
                    self.id = metadata["id"]
                if "summary" in metadata:
                    self.summary = metadata["summary"]
                if "description" in metadata:
                    self.description = metadata["description"]
                if "categories" in metadata:
                    self.categories = metadata["categories"]
                if "parameters" in metadata:
                    self.parameters = []
                    for key, value in metadata["parameters"]:
                        param = Parameter()
                        param.from_metadata(value, version)
                        param.name = key
                        self.parameters.append(param)
                if "returns" in metadata:
                    self.returns = metadata["returns"]
                if "deprecated" in metadata:
                    self.deprecated = metadata["deprecated"]
                if "experimental" in metadata:
                    self.experimental = metadata["experimental"]
                if "exceptions" in metadata:
                    self.exceptions = metadata["exceptions"]
                if "examples" in metadata:
                    self.examples = metadata["examples"]
                if "links" in metadata:
                    self.links = metadata["links"]


class Parameter:

    name = None
    description = None
    optional = None
    deprecated = None
    experimental = None
    default = None
    schema = {}

    def __init__(self):
        pass

    def from_metadata(self, metadata, version):

        if version.at_least("1.0.0"):
            if "name" in metadata:
                self.name = metadata["name"]
            if "description" in metadata:
                self.description = metadata["description"]
            if "optional" in metadata:
                self.optional = metadata["optional"]
            if "deprecated" in metadata:
                self.deprecated = metadata["deprecated"]
            if "experimental" in metadata:
                self.experimental = metadata["experimental"]
            if "default" in metadata:
                self.default = metadata["default"]
            if "schema" in metadata:
                self.schema = metadata["schema"]
        else:
            if "description" in metadata:
                self.description = metadata["description"]
            if "required" in metadata:
                self.optional = not metadata["required"]
            if "deprecated" in metadata:
                self.deprecated = metadata["deprecated"]
            if "experimental" in metadata:
                self.experimental = metadata["experimental"]
            if "schema" in metadata:
                self.schema = metadata["schema"]

    def get_type(self):

        if "subtype" in self.schema:
            return self.schema["subtype"]
        elif "type" in self.schema:
            if isinstance(self.schema["type"], list):
                return list_to_lang(self.schema["type"])
            else:
                return self.schema["type"]
        elif isinstance(self.schema, list):
            type_list = []
            for item in self.schema:
                if "subtype" in item:
                    type_list.append(item["subtype"])
                elif "type" in item:
                    type_list.append(item["type"])
            return list_to_lang(type_list)
        else:
            return self.schema["description"]


# class ProcessInfo:
#
#     id = None
#
#     def __init__(self, id, parameters=None, desc=None, returns=None, returns_desc=None):
#         self.id = id
#         if parameters:
#             self.parameters = parameters
#         else:
#             self.parameters = []
#
#         self.desc = desc
#         self.returns = returns
#         self.returns_desc = returns_desc
