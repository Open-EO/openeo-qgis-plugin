

class Job():

    def __init__(self, process_graph=None, title=None):
        self.title = title
        self.process_graph = process_graph


class Parameter:

    def __init__(self, name=None, type=None, required=False, desc=None, example=None):
        self.name = name
        self.type = type
        self.required = required
        self.example = example
        self.desc = desc


class Process():

    def __init__(self, id, parameters=None, desc=None, returns=None, returns_desc=None):
        self.id = id
        if parameters:
            self.parameters = parameters
        else:
            self.parameters = []

        self.desc = desc
        self.returns = returns
        self.returns_desc = returns_desc
