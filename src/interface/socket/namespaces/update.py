

from flask_socketio import Namespace


class UpdateEventNamespace(Namespace):

    def __init__(self):
        super().__init__('/update')
