import logging
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from sunarp.sunarp_client import SunarpClient, SunarpNotFound
from reniec.client import ReniecClient
from pide_client.sunarp.sunarp_client import SunarpClient
from pide_client.sunat.sunat_client import SunatClient

# Importa la excepción SunarpNotFound si está definida en el módulo correspondiente
try:
    from pide_client.sunarp.sunarp_client import SunarpNotFound
except ImportError:
    class SunarpNotFound(Exception):
        pass

# ===============================
# Configuración de Logging
# ===============================
if not os.path.exists("logs"):
    os.makedirs("logs")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("logs/app.log", encoding="utf-8"),
        logging.StreamHandler()  # opcional: también muestra en consola
    ]
)

logger = logging.getLogger(__name__)

# ===============================
# Configuración de la app Flask
# ===============================
app = Flask(__name__)
app.secret_key = "a9f84jf09w8ehfw0n32r9uhwef9u"

@app.route("/")
def index():
    logger.info("Ingreso al menú principal")
    return render_template("index.html")

# ===============================
# RENIEC
# ===============================
@app.route("/reniec", methods=["GET", "POST"])
def reniec():
    if request.method == "POST":
        dni = request.form.get("dni")
        client = ReniecClient()
        try:
            resp = client.consultar_dni(dni)
            data = resp["consultarResponse"]["return"]["datosPersona"]
            logger.info(f"Consulta RENIEC exitosa para DNI: {dni}")
            return render_template("result_reniec.html", persona=data)
        except Exception as e:
            logger.error(f"Error en consulta RENIEC para DNI {dni}: {e}", exc_info=True)
            return render_template("reniec.html", error=str(e))
    logger.info("Ingreso a formulario RENIEC")
    return render_template("reniec.html")

# ===============================
# SUNARP - Página principal
# ===============================
@app.route("/sunarp", methods=["GET", "POST"])
def sunarp():
    logger.info("Ingreso a formulario SUNARP")
    return render_template("sunarp.html")


# 🚗 Página del formulario de consulta por placa
@app.route("/sunarp/placa", methods=["POST"])
def buscar_por_placa():
    placa = request.form.get("placa", "").strip().upper()
    if not placa:
        flash("Debe ingresar una placa", "warning")
        return redirect(url_for("sunarp"))

    sunarp_client = SunarpClient()
    try:
        resultado = sunarp_client.consulta_placa_global(placa)
        return render_template("result_sunarp.html", tipo="placa", data=resultado)
    except SunarpNotFound:
        flash("No se encontró información para la placa ingresada", "danger")
        return redirect(url_for("index"))
    
    
# 🏢 Consulta Persona Jurídica
@app.route("/sunarp/pj", methods=["POST"])
def consulta_pj():
    razon_social = request.form.get("razon_social", "").strip()
    if not razon_social:
        return render_template("sunarp.html", error="Debe ingresar una razón social")

    client = SunarpClient()
    try:
        resp = client.consulta_persona_juridica_soap(razon_social)
        if not resp or not resp.get("denominacion"):
            return render_template("sunarp.html", error="No se encontraron resultados en SUNARP")
        
        logger.info(f"Consulta SUNARP exitosa - Persona Jurídica (SOAP): {razon_social}")
        return render_template("result_sunarp.html", tipo="pj", data=resp)

    except Exception as e:
        logger.error(f"Error en consulta SUNARP Persona Jurídica {razon_social}: {e}", exc_info=True)
        return render_template("sunarp.html", error="Error al consultar SUNARP, intente nuevamente.")


# 🏢 Listar Oficinas
@app.route("/sunarp/oficinas", methods=["GET"])
def listar_oficinas():
    client = SunarpClient()
    try:
        resp = client.listar_oficinas()
        logger.info("Consulta SUNARP exitosa - Listado de oficinas")
        return render_template("result_sunarp.html", tipo="oficinas", data=resp)
    except Exception as e:
        logger.error(f"Error en consulta SUNARP Listar Oficinas: {e}", exc_info=True)
        return render_template("sunarp.html", error=str(e))


# 🏠 Consulta de Titularidad (SOAP)
@app.route("/sunarp/titularidad", methods=["POST"])
def consulta_titularidad_route():
    tipo_participante = request.form.get("tipo_participante", "").upper().strip()
    apellido_paterno = request.form.get("apellido_paterno", "").strip().upper()
    apellido_materno = request.form.get("apellido_materno", "").strip().upper()
    nombres = request.form.get("nombres", "").strip().upper()
    razon_social = request.form.get("razon_social", "").strip().upper()

    if tipo_participante not in ("N", "J"):
        return render_template("sunarp.html", error="Debe seleccionar el tipo de participante (N o J)")

    client = SunarpClient()
    try:
        resp = client.consulta_titularidad_soap(
            tipo_participante=tipo_participante,
            apellido_paterno=apellido_paterno if tipo_participante == "N" else None,
            apellido_materno=apellido_materno if tipo_participante == "N" else None,
            nombres=nombres if tipo_participante == "N" else None,
            razon_social=razon_social if tipo_participante == "J" else None,
        )

        if not resp:
            return render_template("sunarp.html", error="No se encontraron bienes registrados en SUNARP")

        logger.info(f"Consulta SUNARP exitosa - Titularidad {tipo_participante}")
        return render_template("result_sunarp.html", tipo="titularidad", data=resp)

    except Exception as e:
        logger.error(f"Error en consulta SUNARP Titularidad: {e}", exc_info=True)
        return render_template("sunarp.html", error="Error al consultar SUNARP, intente nuevamente.")
    

# ===============================
# SUNAT - Consulta de RUC
# ===============================
@app.route("/sunat", methods=["GET", "POST"])
def sunat():
    data = None
    error = None

    if request.method == "POST":
        ruc = request.form.get("ruc", "").strip()
        if not ruc:
            error = "Debe ingresar un RUC"
        else:
            client = SunatClient()
            data = client.consulta_ruc(ruc)
            if not data:
                error = "No se encontró información para ese RUC"

    return render_template("sunat.html", data=data, error=error)


# ===============================
# Entrypoint
# ===============================
def main():
    logger.info("Iniciando aplicación Flask en puerto 5000")
    app.run(debug=True, port=5000)

if __name__ == "__main__":
    main()