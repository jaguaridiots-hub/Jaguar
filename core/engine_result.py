class EngineResult:

    def __init__(
        self,
        name,
        signal="NEUTRAL",
        score=0,
        confidence=0.0,
        weight=1.0,
        reasons=None,
        metadata=None,
    ):

        self.name = name
        self.signal = signal
        self.score = score
        self.confidence = confidence
        self.weight = weight

        self.reasons = reasons or []

        self.metadata = metadata or {}

    def to_dict(self):

        return {

            "name": self.name,

            "signal": self.signal,

            "score": self.score,

            "confidence": self.confidence,

            "weight": self.weight,

            "reasons": self.reasons,

            "metadata": self.metadata,

        }
