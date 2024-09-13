

from flask_socketio import Namespace

from server import Server


class UpdateEventNamespace(Namespace):

    def __init__(self, server: Server):
        super().__init__('/update')
        self._server = server
