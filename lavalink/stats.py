class Penalty:
    """
    Represents the penalty of the stats of a Node.

    Attributes
    ----------
    player_penalty: :class:`int`
    cpu_penalty: :class:`int`
    null_frame_penalty: :class:`int`
    deficit_frame_penalty: :class:`int`
    total: :class:`int`
    """
    __slots__ = ('player_penalty', 'cpu_penalty', 'null_frame_penalty', 'deficit_frame_penalty', 'total')

    def __init__(self, stats):
        self.player_penalty = stats.playing_players
        self.cpu_penalty = 1.05 ** (100 * stats.system_load) * 10 - 10
        self.null_frame_penalty = 0
        self.deficit_frame_penalty = 0

        if stats.frames_nulled is not -1:
            self.null_frame_penalty = (1.03 ** (500 * (stats.frames_nulled / 3000))) * 300 - 300
            self.null_frame_penalty *= 2

        if stats.frames_deficit is not -1:
            self.deficit_frame_penalty = (1.03 ** (500 * (stats.frames_deficit / 3000))) * 600 - 600

        self.total = self.player_penalty + self.cpu_penalty + self.null_frame_penalty + self.deficit_frame_penalty


class Stats:
    """
    Represents the stats of Lavalink node.

    Attributes
    ----------
    uptime: :class:`int`
        How long the node has been running for in milliseconds.
    players: :class:`int`
        The amount of players connected to the node.
    playing_players: :class:`int`
        The amount of players that are playing in the node.
    memory_free: :class:`int`
        The amount of memory free to the node.
    memory_used: :class:`int`
        The amount of memory that is used by the node.
    memory_allocated: :class:`int`
        The amount of memory allocated to the node.
    memory_reservable: :class:`int`
        The amount of memory reservable to the node.
    cpu_cores: :class:`int`
        The amount of cpu cores the system of the node has.
    system_load: :class:`int`
    lavalink_load: :class:`int`
    frames_sent: :class:`int`
    frames_nulled: :class:`int`
    frames_deficit: :class:`int`
    penalty: :class:`Penalty`
    """
    __slots__ = ('_node', 'uptime', 'players', 'playing_players', 'memory_free', 'memory_used', 'memory_allocated',
                 'memory_reservable', 'cpu_cores', 'system_load', 'lavalink_load', 'frames_sent', 'frames_nulled',
                 'frames_deficit', 'penalty')

    def __init__(self, node, data):
        self._node = node

        self.uptime = data['uptime']

        self.players = data['players']
        self.playing_players = data['playingPlayers']

        memory = data['memory']
        self.memory_free = memory['free']
        self.memory_used = memory['used']
        self.memory_allocated = memory['allocated']
        self.memory_reservable = memory['reservable']

        cpu = data['cpu']
        self.cpu_cores = cpu['cores']
        self.system_load = cpu['systemLoad']
        self.lavalink_load = cpu['lavalinkLoad']

        frame_stats = data.get('frameStats', {})
        self.frames_sent = frame_stats.get('sent', -1)
        self.frames_nulled = frame_stats.get('nulled', -1)
        self.frames_deficit = frame_stats.get('deficit', -1)
        self.penalty = Penalty(self)
