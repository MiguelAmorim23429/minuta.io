"""Motor local do minuta.io.

Corre como processo filho da aplicação Tauri e comunica exclusivamente por JSON-RPC 2.0
sobre stdin/stdout. Não abre portas de rede.
"""

__version__ = "0.1.0"
