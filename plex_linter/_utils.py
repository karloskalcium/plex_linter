# misc utility functions

# from https://stackoverflow.com/q/1034573/4907881
def xstr(s) -> str:
    """Returns string of object or empty string if None"""
    if s is None:
        return ""
    else:
        return str(s)
