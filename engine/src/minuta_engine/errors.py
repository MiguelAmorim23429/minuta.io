"""Erros devolvidos à interface."""

# Códigos de erro definidos pela especificação JSON-RPC 2.0.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
# Erro de aplicação (intervalo reservado a servidores pela especificação).
APP_ERROR = -32000


class RpcError(Exception):
    """Erro a devolver ao cliente com um código específico."""

    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class UserError(Exception):
    """Problema que o utilizador consegue resolver (ficheiro inválido, campo em falta…).

    A mensagem é mostrada ao utilizador, mas **nunca** é escrita nos logs.
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
