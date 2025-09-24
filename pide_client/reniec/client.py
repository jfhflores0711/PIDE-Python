import logging
import requests
from . import config
from .exceptions import ReniecError, CredencialCaducadaError, UsuarioNoValidoError

logger = logging.getLogger(__name__)

class ReniecClient:
    def __init__(self, ruc=config.RUC, user_dni=config.USER_DNI, password=config.PASSWORD):
        self.base_url = config.BASE_URL
        self.ruc = ruc
        self.user_dni = user_dni
        self.password = password

    def actualizar_credencial(self, credencial_anterior, credencial_nueva):
        url = f"{self.base_url}/Actualizar?out=json"
        payload = {
            "PIDE": {
                "credencialAnterior": credencial_anterior,
                "credencialNueva": credencial_nueva,
                "nuDni": self.user_dni,
                "nuRuc": self.ruc
            }
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if "coResultado" in data and data["coResultado"] != "0000":
                raise ReniecError(f"Error al actualizar credencial: {data}")
            logger.info("RENIEC - credencial actualizada correctamente")
            return data
        except Exception as e:
            logger.error(f"RENIEC - error al actualizar credencial: {e}", exc_info=True)
            raise

    def consultar_dni(self, dni_consulta):
        url = f"{self.base_url}/Consultar?out=json"
        payload = {
            "PIDE": {
                "nuDniConsulta": dni_consulta,
                "nuDniUsuario": self.user_dni,
                "nuRucUsuario": self.ruc,
                "password": self.password
            }
        }
        try:
            resp = requests.post(url, json=payload, headers={"Content-Type": "application/json"}, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            if "coResultado" in data and data["coResultado"] != "0000":
                code = data["coResultado"]
                if code == "1002":
                    raise CredencialCaducadaError("La contraseña ha caducado.")
                elif code == "1001":
                    raise UsuarioNoValidoError("Usuario o credenciales inválidas.")
                else:
                    raise ReniecError(f"Error en consulta DNI: {data}")
            logger.info(f"RENIEC - consulta exitosa para DNI {dni_consulta}")
            return data
        except Exception as e:
            logger.error(f"RENIEC - error en consulta DNI {dni_consulta}: {e}", exc_info=True)
            raise
