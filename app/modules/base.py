from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ProcessResult:
    document_id: str
    ok: bool
    error: str = ""
    file_path: str = ""
    duration: float = 0.0


class DocumentModule(ABC):
    module_id = ""
    module_name = ""

    @abstractmethod
    def validate_ids(self, lines):
        ...

    @abstractmethod
    def process_one(self, session, document_id, context):
        ...