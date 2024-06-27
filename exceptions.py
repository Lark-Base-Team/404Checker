class FieldError(Exception):
    def __init__(self, msg):
        self.msg = msg


class PersonalBaseTokenError(Exception):
    def __init__(self, msg):
        self.msg = msg
