def permission(code: str):
    def decorator(func):
        setattr(func, "__permission_code__", code)
        return func
    
    return decorator
