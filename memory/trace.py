import logging

logger = logging.getLogger("papper-memory")

class MemoryManager:
    """The Experience: Tracking history to prevent infinite loops."""
    def __init__(self):
        self.history = []
        self.action_log = []

    def record_action(self, action_dict, result_dict):
        """Log an action and its outcome."""
        summary = f"Action: {action_dict['action_type']}"
        if action_dict.get('index'): summary += f" on [{action_dict['index']}]"
        if action_dict.get('text'): summary += f" with '{action_dict['text']}'"
        
        status = result_dict.get('status', 'unknown')
        msg = result_dict.get('message', '')
        
        entry = f"{summary} -> {status.upper()}: {msg}"
        self.history.append(entry)
        self.action_log.append({"action": action_dict, "result": result_dict})
        
        if len(self.history) > 20:
            self.history.pop(0)

    def is_stuck(self):
        """Heuristic to detect if we are repeating the same failed actions."""
        if len(self.action_log) < 3:
            return False

        last_three = self.action_log[-3:]
        first_action = last_three[0]['action']
        first_action_type = first_action.get('action_type')
        first_index = first_action.get('index')

        # If last 3 actions are identical (same type + index) and all failed
        return all(
            x['action'].get('action_type') == first_action_type and
            x['action'].get('index') == first_index and
            x['result']['status'] == 'error'
            for x in last_three
        )

    def get_history_summary(self):
        return "\n".join(self.history)
