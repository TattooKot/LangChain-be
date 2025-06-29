from typing import List, Dict

class ConversationRepository:
    def __init__(self):
        # {conversation_id: [{"role":..., "content":...}, ...]}
        self._store: Dict[str, List[Dict[str, str]]] = {}

    def get_history(self, conv_id: str) -> List[Dict[str, str]]:
        return self._store.setdefault(conv_id, [])

    def append_user(self, conv_id: str, message: str) -> None:
        self.get_history(conv_id).append({"role": "user", "content": message})

    def append_assistant(self, conv_id: str, message: str) -> None:
        self.get_history(conv_id).append({"role": "assistant", "content": message})
