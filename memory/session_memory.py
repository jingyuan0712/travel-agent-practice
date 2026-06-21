class SessionMemory:
    def __init__(self):
        """Initialize empty session memory for travel planning details."""
        self.memory = {
            "city": None,
            "days": None,
            "style": None,
            "budget": None,
            "travelers": None
        }

    def update_memory(self, **kwargs) -> dict:
        """Updates memory with new key-value pairs, merging with existing data.
        
        Ignores parameters that are None or not defined in the schema.
        """
        for key, value in kwargs.items():
            if key in self.memory and value is not None:
                # Convert numeric values to integer if possible
                if key in ["days", "budget", "travelers"]:
                    try:
                        self.memory[key] = int(value)
                    except (ValueError, TypeError):
                        self.memory[key] = value
                else:
                    self.memory[key] = str(value)
        return self.memory

    def get_memory(self) -> dict:
        """Returns the current stored travel parameters."""
        return self.memory

    def clear_memory(self) -> None:
        """Resets all memory fields to None."""
        self.memory = {
            "city": None,
            "days": None,
            "style": None,
            "budget": None,
            "travelers": None
        }

    def show_memory(self) -> dict:
        """Returns the dictionary representation of memory for display purposes."""
        # Return a copy to prevent external mutation
        return self.memory.copy()
