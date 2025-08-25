from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# ------------------------------
# Función para obtener precio Farma.uy
# ------------------------------
def precio_farmacia(producto):
    url = f"https://www.farma.uy/catalogsearch/result/?q={producto}"
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(r.text, "html.parser")
    precio_tag = soup.find("span", class_="price")  # Revisar clase si cambia la web

    if precio_tag:
        texto = precio_tag.text.replace("$", "").replace(".", "").replace(",", ".").strip()
        try:
            precio = float(texto)
            return {"fuente": "FarmaUy", "producto": producto, "precio": precio, "url": url}
        except ValueError:
            return {"fuente": "FarmaUy", "producto": producto, "precio": None, "url": url}
    return None

# ------------------------------
# Función para obtener precios Mercado Libre
# ------------------------------
import requests
from bs4 import BeautifulSoup

def precios_mercadolibre(producto):
    url = f"https://listado.mercadolibre.com.uy/tienda/farmauy/{producto}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/116.0.0.0 Safari/537.36",
        "Accept-Language": "es-UY,es;q=0.9",
        "Referer": "https://www.mercadolibre.com.uy/"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return []  # Si no devuelve 200, devuelve lista vacía
    
    soup = BeautifulSoup(response.text, "html.parser")
    resultados = []
    
    for item in soup.find_all("li", class_="ui-search-layout__item"):
        nombre_tag = item.select_one(".poly-component__title")
        precio_tag = item.select_one(".andes-money-amount__fraction")
        
        if nombre_tag and precio_tag:
            try:
                # Convertir a float en lugar de int para manejar decimales
                precio_texto = precio_tag.text.replace(".", "").replace(",", ".").strip()
                precio = float(precio_texto)
                resultados.append((nombre_tag.text.strip(), precio))
            except:
                continue
    
    return resultados

# ------------------------------
# Ruta principal
# ------------------------------
@app.route("/", methods=["GET", "POST"])
def index():
    resultados = []
    mejor = None
    producto = ""

    if request.method == "POST":
        producto = request.form["producto"]

        # Farma.uy
        farmacia = precio_farmacia(producto)
        if farmacia:
            resultados.append(farmacia)

        # Mercado Libre
        mercadolibre = precios_mercadolibre(producto)
        resultados.extend(mercadolibre)

        # Determinar el precio más barato
        precios_validos = [r for r in resultados if r["precio"] is not None]
        if precios_validos:
            mejor = min(precios_validos, key=lambda x: x["precio"])

    return render_template("index.html", producto=producto, resultados=resultados, mejor=mejor)

# ------------------------------
# Ejecutar app
# ------------------------------
if __name__ == "__main__":
    app.run(debug=True)
