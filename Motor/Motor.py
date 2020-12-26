class Motor:
    """Interface für alle Motoren. Design noch nicht endgültig."""

    @property
    def nameDesMotors(self):
        raise NotImplementedError

    @property
    def anschlussDesMotors(self):
        raise NotImplementedError
