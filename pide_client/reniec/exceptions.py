class ReniecError(Exception):
    """Error genérico del cliente RENIEC"""
    pass


class CredencialCaducadaError(ReniecError):
    """La credencial ha caducado"""
    pass


class UsuarioNoValidoError(ReniecError):
    """El DNI/RUC/clave no corresponde a un usuario válido"""
    pass