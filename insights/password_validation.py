import re

from django.core.exceptions import ValidationError


class PasswordValidator(object):
    """
    Validate whether the password is of a minimum length.
    """
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])((?=.*\d)|(?=.*(_|[^\w]))).+$'
        match = re.search(pattern, password)
        if not match or not match.group(0) == password:
            raise ValidationError(
                "Your password must include upper and lower letters and numbers or symbol character")

    def get_help_text(self):
        return "Your password must include upper and lower letters and numbers or symbol character"
            