"""Собственные исключения."""


class TokenError(Exception):
    """Исключение поднимается в случае, если отсутствует хотя бы одна
    из обязательных переменных окружения при запуске бота."""

    def __init__(
            self,
            env,
            message='Отсутствует обязательная переменная окружения'
    ):
        self.message = message
        self.token = self.check_token(env)
        super().__init__(self.message)

    def __str__(self):
        return f'Отсутствует обязательная переменная окружения: ' \
               f'{self.token}. Программа принудительно остановлена.'

    def check_token(self, env):
        token_list = ['PRACTICUM_TOKEN', 'TELEGRAM_TOKEN', 'TELEGRAM_CHAT_ID']
        for token in token_list:
            if token not in env:
                return token


class StatusError(Exception):
    """Исключение поднимается в случае, если обнаружен
     недокументированный статус домашней работы."""

    def __init__(
            self,
            message='Недокументированный статус домашней работы'
    ):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return 'Недокументированный статус домашней работы'
