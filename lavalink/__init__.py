__title__ = 'Lavalink'
__author__ = 'Luke & William'
__license__ = 'MIT'
__copyright__ = 'Copyright 2018 Luke & William'
__version__ = '2.1'
__modified__ = "By: Andraž Korenč"
import sys

from .AudioTrack import *
from .Client import *
from .Events import *
from .PlayerManager import *
from .Utils import *
from .WebSocket import *

log = logging.getLogger(__name__)

fmt = logging.Formatter(
    '[%(asctime)s] [lavalink.py] [%(levelname)s] %(message)s',
    datefmt="%H:%M:%S"
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(fmt)
log.addHandler(handler)

log.setLevel(logging.INFO)
