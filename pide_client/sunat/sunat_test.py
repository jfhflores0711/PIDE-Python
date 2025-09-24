import requests

ruc = "20100032458"  # Ejemplo: Telefónica
url = f"https://api.apis.net.pe/v1/ruc?numero={ruc}"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()
    print("✅ Datos del RUC:")
    print(f"RUC: {data.get('numero')}")
    print(f"Razón Social: {data.get('nombre')}")
    print(f"Estado: {data.get('estado')}")
    print(f"Condición: {data.get('condicion')}")
    print(f"Dirección: {data.get('direccion')}")
else:
    print(f"❌ Error {response.status_code}: {response.text}")