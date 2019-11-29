class Crb():
    def __init__(self, hostname, username, password, port=22, timeout=10):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout