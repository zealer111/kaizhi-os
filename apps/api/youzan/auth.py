
class Auth:
    def __init__(self):
        pass

class Sign(Auth):
    def __init__(self, app_id, app_secret):
        self.app_id = '1b4cb35ecc953f5116'
        self.app_secret = '8be7d0858edd4eda2ba979558ef0a38c'

    def get_app_id(self):
        return self.app_id

    def get_app_secret(self):
        return self.app_secret


class Token(Auth):
    def __init__(self, token):
        self.token = token

    def get_token(self):
        return self.token

