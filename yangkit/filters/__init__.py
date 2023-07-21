import enum


class YFilter(enum.Enum):
    """
    Different YANG filter types
    """
    merge = 'merge'
    create = 'create'
    remove = 'remove'
    delete = 'delete'
    replace = 'replace'
    not_set = 'not_set'
