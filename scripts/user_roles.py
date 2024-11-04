# user_roles.py

from enum import Enum, auto

class UserRole(Enum):
    ADMIN = auto()
    TEACHER = auto()
    STUDENT = auto()

class UserRoles:
    def __init__(self):
        self.roles = {}

    def add_role(self, user_id: str, role: UserRole) -> None:
        self.roles[user_id] = role

    def get_role(self, user_id: str) -> UserRole:
        return self.roles.get(user_id, UserRole.STUDENT)  # Default role is STUDENT

    def remove_role(self, user_id: str) -> None:
        if user_id in self.roles:
            del self.roles[user_id]

    def is_teacher(self, user_id: str) -> bool:
        return self.roles.get(user_id) == UserRole.TEACHER

    def is_admin(self, user_id: str) -> bool:
        return self.roles.get(user_id) == UserRole.ADMIN

