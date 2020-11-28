class BaseBatchfile:
    def __init__(self, filename):
        self.filename = filename
        self.__dict = {"filename": filename}

    def set(self, key, value):
        self.__dict[key] = value

    def get(self, key, default = None):
        if key in self.__dict:
            return self.__dict[key]
        return default

    def get_state(self):
        return self.__dict

    def set_jobid(self, jobid):
        self.set("jobid", jobid)

    def get_jobid(self):
        return get("jobid")

    def get_filename(self):
        return self.filename
