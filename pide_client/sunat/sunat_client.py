import requests
import logging

logger = logging.getLogger(__name__)

class SunatClient:
    BASE_URL = "https://api.apis.net.pe/v1/ruc"

    def __init__(self, token=None):
        self.token = token

    def consulta_ruc(self, ruc: str):
        """
        Consulta el RUC en la API de SUNAT (versión pública de prueba).
        """
        url = f"{self.BASE_URL}?numero={ruc}"
        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        logger.info(f"Consultando RUC {ruc} en SUNAT...")
        resp = requests.get(url, headers=headers)

        if resp.status_code == 200:
            return resp.json()
        else:
            logger.error(f"Error {resp.status_code}: {resp.text}")
            return None