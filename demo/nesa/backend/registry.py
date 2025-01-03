
class ModelRegistry:
    registry = {
        "model_specific": {},
        "task_type": {}
    }

    @classmethod
    def register(cls, key, is_model_specific=False):
        """Register a model class either by model name or by task type."""
        def decorator(wrapped_class):
            if is_model_specific:
                if key in cls.registry["model_specific"]:
                    print(f"Warning: A class is already registered for the model name '{key}'. Overwriting...")
                cls.registry["model_specific"][key] = wrapped_class
            else:
                if key in cls.registry["task_type"]:
                    print(f"Warning: A class is already registered for the task type '{key}'. Overwriting...")
                cls.registry["task_type"][key] = wrapped_class
            return wrapped_class
        return decorator

    @classmethod
    def get_model(cls, base_id, task_type):
        """Get a model class, first by model name, then by task type."""
        if base_id in cls.registry["model_specific"]:
            return cls.registry["model_specific"][base_id]
        elif task_type in cls.registry["task_type"]:
            return cls.registry["task_type"][task_type]
        else:
            raise ValueError(f"No model class found for model '{base_id}' or task type '{task_type}'")

