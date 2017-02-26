import uuid


class PsrpClient(object):

    def __init__(self):
        self.runspacepool_table = {}


class RunspacePool(object):
    def __init__(self):
        self.shell_id = uuid.uuid4()
        self.pipeline_table = {}

class Pipeline(object):
    def __init__(self):
        self.pipeline_id = uuid.uuid4()
