"""Views package for Discord UI components"""

from views.dialogue import DialogueView
from views.enrollment import EnrollmentView, create_enrollment_embed
from views.graduation import GraduationActionsView, create_graduation_embed

__all__ = [
    "DialogueView",
    "EnrollmentView",
    "GraduationActionsView",
    "create_enrollment_embed",
    "create_graduation_embed",
]
