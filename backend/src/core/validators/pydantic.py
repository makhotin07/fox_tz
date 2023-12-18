import re


class PydanticValidator:
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Неверный формат')
        pattern = r'^(?=.*[a-zA-Z])[a-zA-Z0-9!@#$%^&*()-_=+{}[\]|;:<>,.?/~]+$'
        if not re.match(pattern, v):
            raise ValueError('Неверный формат')
        return v

    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Неверный формат')
        pattern = r'^(?=.*[a-zA-Z])[a-zA-Z0-9-_]+$'
        if not re.match(pattern, v):
            raise ValueError('Неверный формат')
        return v
