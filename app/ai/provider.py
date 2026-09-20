from abc import ABC, abstractmethod

from app.ai.context import ActivityContext
from app.ai.schemas import ActivitySummaryResponse


class AIProvider(ABC):
    @abstractmethod
    def generate_activity_summary(
        self,
        context: ActivityContext,
    ) -> ActivitySummaryResponse:
        raise NotImplementedError