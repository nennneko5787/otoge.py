from .client import KonamiClient


class PolarisChord:
    def __init__(self, client: KonamiClient):
        self.client = client
