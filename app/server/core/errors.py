class RouteError(Exception):
    def __init__(self, message: str, code: str = "invalid_request", status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.type = "invalid_request_error" if status < 500 else "server_error"


class WorkerError(Exception):
    def __init__(self, message: str, code: str = "worker_error", status: int = 502):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.type = "server_error"
