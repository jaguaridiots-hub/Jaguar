class EngineResult:

    def __init__(

        self,

        score=0,

        confidence=0,

        signal="HOLD",

        reasons=None,

        metadata=None

    ):

        self.score = score

        self.confidence = confidence

        self.signal = signal

        self.reasons = reasons or []

        self.metadata = metadata or {}

    def to_dict(self):

        return {

            "score": self.score,

            "confidence": self.confidence,

            "signal": self.signal,

            "reasons": self.reasons,

            "metadata": self.metadata

        }
