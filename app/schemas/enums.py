from enum import Enum

class DeleteMode(str, Enum):
    cascade = "cascade"
    reassign = "reassign"