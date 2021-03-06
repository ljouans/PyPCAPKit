# -*- coding: utf-8 -*-
# pylint: disable=line-too-long
"""HIP NAT Traversal Modes"""

from aenum import IntEnum, extend_enum

__all__ = ['NATTraversal']


class NATTraversal(IntEnum):
    """[NATTraversal] HIP NAT Traversal Modes"""

    _ignore_ = 'NATTraversal _'
    NATTraversal = vars()

    #: [:rfc:`5770`]
    NATTraversal['Reserved'] = 0

    #: [:rfc:`5770`]
    NATTraversal['UDP-ENCAPSULATION'] = 1

    #: [:rfc:`5770`]
    NATTraversal['ICE-STUN-UDP'] = 2

    @staticmethod
    def get(key, default=-1):
        """Backport support for original codes."""
        if isinstance(key, int):
            return NATTraversal(key)
        if key not in NATTraversal._member_map_:  # pylint: disable=no-member
            extend_enum(NATTraversal, key, default)
        return NATTraversal[key]

    @classmethod
    def _missing_(cls, value):
        """Lookup function used when value is not found."""
        if not (isinstance(value, int) and 0 <= value <= 65535):
            raise ValueError('%r is not a valid %s' % (value, cls.__name__))
        if 3 <= value <= 65535:
            extend_enum(cls, 'Unassigned [%d]' % value, value)
            return cls(value)
        return super()._missing_(value)
