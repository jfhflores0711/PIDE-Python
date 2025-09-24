import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://ws2.pide.gob.pe/Rest/RENIEC"

# Variables de entorno (poner en archivo .env)
RUC = os.getenv("RENIEC_RUC")
USER_DNI = os.getenv("RENIEC_USER_DNI")  # DNI usuario habilitado
PASSWORD = os.getenv("RENIEC_PASSWORD")  # Clave (debe actualizarse cada 15 días)