import os
import json
import logging
from dotenv import load_dotenv
import requests
from zeep import Client, Settings
from zeep.transports import Transport
from requests import Session
from lxml import etree  # 👈 para parsear la respuesta SOAP en bruto
from zeep.helpers import serialize_object

# ---------------- Utilidad: normalizar textos ----------------
def _normalize_text(value):
    if isinstance(value, str):
        try:
            return value.encode("latin-1").decode("utf-8")
        except UnicodeDecodeError:
            try:
                return value.encode("utf-8").decode("latin-1")
            except UnicodeDecodeError:
                try:
                    return value.encode("latin-1").decode("latin-1")
                except UnicodeDecodeError:
                    return value
    return value



# ---------------- Cargar variables de entorno ----------------
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---------------- Excepciones específicas ----------------
class SunarpError(Exception):
    """Error general en SUNARP"""
    pass

class SunarpAuthError(SunarpError):
    """Error de autenticación (usuario/clave/IP)"""
    pass

class SunarpNotFound(SunarpError):
    """No se encontraron resultados"""
    pass

class SunarpPermissionError(SunarpError):
    """Error de permisos"""
    pass


# ---------------- Cliente SUNARP ----------------
class SunarpClient:
    BASE_URL_REST = "https://ws2.pide.gob.pe/Rest/SUNARP"
    WSDL_URL = "https://ws2.pide.gob.pe/services/SUNARPWSService?wsdl"

    def __init__(self):
        self.user = os.getenv("SUNARP_USER")
        self.password = os.getenv("SUNARP_PASS")

        if not self.user or not self.password:
            raise ValueError("Faltan credenciales SUNARP en .env")

        self.soap = None

      
    # ---------------- REST genérico ----------------
    def _rest_request(self, endpoint, payload=None, method="POST"):
        url = f"{self.BASE_URL_REST}/{endpoint}?out=json"

        # Cuerpo base con credenciales
        data = {"PIDE": {"usuario": self.user.strip(), "clave": self.password.strip()}}
        if payload:
            data["PIDE"].update(payload)

        headers = {"Content-Type": "application/json", "Accept": "application/json"}

        try:
            if method.upper() == "POST":
                #body = json.dumps(data, ensure_ascii=False)
                #logger.warning(f"Payload enviado a {endpoint}: {body}")
                #resp = requests.post(url, headers=headers, data=body, timeout=30)
                logger.warning(f"Payload enviado a {endpoint}: {json.dumps(data, ensure_ascii=False)}")
                resp = requests.post(url, headers=headers, json=data, timeout=30)
            else:
                resp = requests.get(url, params=data["PIDE"], headers=headers, timeout=30)

            logger.info(f"REST {method} {url} -> {resp.status_code}")
            resp.raise_for_status()

            response = resp.json()
            self._check_response_errors(response)
            return response

        except Exception as e:
            logger.error(f"REST error en {endpoint}: {e}", exc_info=True)
            raise

    # ---------------- SOAP genérico ----------------
    def _get_soap_client(self):
        if self.soap is None:
            logger.info("Inicializando cliente SOAP SUNARP...")
            session = Session()
            transport = Transport(session=session, timeout=30)
            settings = Settings(strict=False, xml_huge_tree=True)
            self.soap = Client(self.WSDL_URL, transport=transport, settings=settings)
        return self.soap

    def _soap_call(self, method, **kwargs):
        client = self._get_soap_client()
        logger.info(f"SOAP llamada {method} con {kwargs}")
        try:
            result = getattr(client.service, method)(usuario=self.user, clave=self.password, **kwargs)
            if isinstance(result, str):
                self._check_response_errors(result)
            return result
        except Exception as e:
            logger.error(f"SOAP error en {method}: {e}", exc_info=True)
            raise

    # ---------------- Validación de errores ----------------
    def _check_response_errors(self, response):
        if not response:
            raise SunarpError("Respuesta vacía de SUNARP")

        if isinstance(response, dict):
            if "Respuesta" in response and "Error" in response["Respuesta"]:
                msg = response["Respuesta"]["Error"]
                msg_lower = msg.lower()
                if "usuario o password" in msg_lower:
                    raise SunarpAuthError(msg)
                if "permiso" in msg_lower:
                    raise SunarpPermissionError(msg)
                if "no existe" in msg_lower:
                    raise SunarpNotFound(msg)
                if "no se pudo determinar el tipo de consulta" in msg_lower:
                    raise SunarpNotFound("No se pudo determinar el tipo de consulta")
                raise SunarpError(msg)

        msg = json.dumps(response) if isinstance(response, dict) else str(response)
        msg_lower = msg.lower()

        if "no se pudo determinar el tipo de consulta" in msg_lower:
            raise SunarpNotFound("No se pudo determinar el tipo de consulta")

        if "usuario o password" in msg_lower:
            raise SunarpAuthError("Usuario o password incorrectos")
        if "ip no autorizada" in msg_lower:
            raise SunarpAuthError("IP no autorizada")
        if "no tiene permiso" in msg_lower:
            raise SunarpPermissionError("Usuario sin permiso")
        if "no existe resultados" in msg_lower:
            raise SunarpNotFound("No se encontraron resultados")


    # ---------------- Métodos públicos ----------------
    def listar_oficinas(self):
        client = self._get_soap_client()
        with client.settings(raw_response=True):
            response = client.service.getOficinas(usuario=self.user, clave=self.password)

            # Convertir a XML y parsear
            root = etree.fromstring(response.content)

            oficinas = []
            for oficina in root.findall(".//oficina"):
                oficinas.append({
                    "codigo": oficina.findtext("codOficina"),
                    "nombre": oficina.findtext("descripcion"),
                    "zona": oficina.findtext("codZona")
                })

            if not oficinas:
                raise SunarpNotFound("El servicio SOAP getOficinas no devolvió resultados")

            logger.info("Consulta SUNARP exitosa - Listado de oficinas")
            return {"oficinas": oficinas}
    


    def consulta_placa_global(self, placa):
        placa = placa.strip().upper()
        oficinas_data = self.listar_oficinas()
        oficinas = oficinas_data.get("oficinas", [])

        for oficina in oficinas:
            try:
                resultado = self.consulta_placa(
                    zona=str(oficina["zona"]).zfill(2),
                    oficina=str(oficina["codigo"]).zfill(2),
                    placa=placa
                )

                # Si encontró vehículo válido (tiene placa y marca por ejemplo)
                if resultado and resultado.get("placa"):
                    #logger.info(f"Vehículo encontrado en oficina {oficina['nombre']} (Zona {oficina['zona']})")
                    resultado["oficina"] = oficina["nombre"]
                    resultado["zona"] = oficina["zona"]
                    return resultado

            except SunarpNotFound:
                continue  # si no hay en esta oficina, sigue probando
            except Exception as e:
                logger.warning(f"Error consultando en oficina {oficina['nombre']}: {e}")
                continue

        # Si no encuentra en ninguna oficina
        raise SunarpNotFound(f"No se encontró información para la placa {placa}")


    def consulta_placa(self, zona, oficina, placa):
        raw_obj = self._soap_call("verDetalleRPVExtra", zona=zona, oficina=oficina, placa=placa)
        raw = serialize_object(raw_obj)

        estado = _normalize_text(raw.get("estado", "")).strip()
        if "circulaci" in estado.lower():
            estado = "En circulación"

        vehiculo = {
            "placa": raw.get("placa", "").strip(),
            "marca": _normalize_text(raw.get("marca")),
            "modelo": _normalize_text(raw.get("modelo")),
            "color": _normalize_text(raw.get("color", "").strip()),
            "carroceria": _normalize_text(raw.get("carroceria")),
            "estado": estado,
            "anoFabricacion": raw.get("anoFabricacion").strip() if raw.get("anoFabricacion") and raw.get("anoFabricacion").strip() != "0" else "No registrado",
            "vin": raw.get("vin"),
            "nro_motor": raw.get("nro_motor"),
            "propietarios": raw.get("propietarios", {}).get("nombre", [])
        }

        # Si la placa vino vacía o inválida, lo tratamos como no encontrado
        if not vehiculo["placa"]:
            raise SunarpNotFound(f"No se encontró información para la placa {placa}")

        return vehiculo

    
    
    def consulta_persona_juridica_soap(self, razon_social):
        client = self._get_soap_client()
        try:
            # Usamos raw_response=True para capturar el XML completo (incluye headers)
            with client.settings(raw_response=True):
                response = client.service.buscarPJRazonSocial(
                    usuario=self.user,
                    clave=self.password,
                    razonSocial=razon_social.strip()
                )

                # Parsear el XML devuelto
                from lxml import etree
                root = etree.fromstring(response.content)

                # Buscar dentro de <personaJuridica><resultado>
                resultado = root.find(".//resultado")
                if resultado is None:
                    raise SunarpNotFound("No se encontró información de persona jurídica en SUNARP")

                pj = {
                    "denominacion": resultado.findtext("denominacion"),
                    "tipo": resultado.findtext("tipo"),
                    "zona": resultado.findtext("zona"),
                    "oficina": resultado.findtext("oficina"),
                    "partida": resultado.findtext("partida"),
                    "ficha": resultado.findtext("ficha"),
                    "tomo": resultado.findtext("tomo"),
                    "folio": resultado.findtext("folio"),
                }

                return pj

        except Exception as e:
            logger.error(f"Error en consulta SOAP Persona Jurídica: {e}", exc_info=True)
            raise

    def consulta_titularidad_soap(self, tipo_participante, apellido_paterno=None, apellido_materno=None,
                                  nombres=None, razon_social=None):
        # Validaciones básicas
        tipo = (tipo_participante or "").upper()
        if tipo not in ("N", "J"):
            raise ValueError("tipo_participante debe ser 'N' (natural) o 'J' (jurídica)")

        if tipo == "N" and not apellido_paterno:
            raise ValueError("apellido_paterno es obligatorio para persona natural (tipo 'N')")

        if tipo == "J" and not razon_social:
            raise ValueError("razon_social es obligatorio para persona jurídica (tipo 'J')")

        client = self._get_soap_client()
        logger.info(f"SOAP llamada buscarTitularidadSIRSARP tipo={tipo} apPaterno={apellido_paterno} razonSocial={razon_social}")

        try:
            with client.settings(raw_response=True):
                # Llamada SOAP (nombre según contrato)
                response = client.service.buscarTitularidadSIRSARP(
                    usuario=self.user,
                    clave=self.password,
                    tipoParticipante=tipo,
                    apellidoPaterno=(apellido_paterno or ""),
                    apellidoMaterno=(apellido_materno or ""),
                    nombres=(nombres or ""),
                    razonSocial=(razon_social or "")
                )

                # Parsear XML
                from lxml import etree
                root = etree.fromstring(response.content)

                # Seleccionamos aquellos <respuestaTitularidad> que tengan el hijo <registro>.
                titulares = []
                for node in root.findall(".//respuestaTitularidad"):
                    # skip wrapper nodes sin contenido directo
                    if node.find("registro") is None:
                        continue

                    titulares.append({
                        "registro": node.findtext("registro"),
                        "libro": node.findtext("libro"),
                        "apPaterno": node.findtext("apPaterno"),
                        "apMaterno": node.findtext("apMaterno"),
                        "nombre": node.findtext("nombre"),
                        "razonSocial": node.findtext("razonSocial"),
                        "tipoDocumento": node.findtext("tipoDocumento"),
                        "numeroDocumento": node.findtext("numeroDocumento"),
                        "numeroPartida": node.findtext("numeroPartida"),
                        "numeroPlaca": node.findtext("numeroPlaca"),
                        "estado": node.findtext("estado"),
                        "zona": node.findtext("zona"),
                        "oficina": node.findtext("oficina"),
                        "direccion": node.findtext("direccion"),
                    })

                if not titulares:
                    raise SunarpNotFound("No se encontraron titulares para los parámetros indicados")

                logger.info(f"Consulta Titularidad exitosa. Resultados: {len(titulares)}")
                return titulares

        except Exception as e:
            logger.error(f"Error en consulta SOAP Titularidad: {e}", exc_info=True)
            raise