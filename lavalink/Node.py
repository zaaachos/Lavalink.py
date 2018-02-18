class NodeStatistics:
    def __init__(self):
        self.playing_players = 0
        self.cores = 0
        self.lavalinkLoad = 0
        self.systemLoad = 0
        self.uptime = 0
        self.memory = {}  # Unused for now


class Node:
    def __init__(self, host, ws, rest):
        self.host = host
        self.ws = ws
        self.rest = rest
