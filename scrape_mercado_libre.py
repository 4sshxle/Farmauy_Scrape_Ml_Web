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
def precios_mercadolibre(producto):
    url = f"https://listado.mercadolibre.com.uy/tienda/farmauy/{producto}?sb=storefront_url#D[A:{producto}]"

    # Usamos un proxy uruguayo HIA
    proxies = {
        "http": "http://190.64.77.11:3128",
        "https": "http://190.64.77.11:3128"
    }

    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, proxies=proxies)
    soup = BeautifulSoup(r.text, "html.parser")

    resultados = []
    items = soup.select("li.ui-search-layout__item")

    for item in items:
        titulo_tag = item.select_one("h3 a")
        precio_tag = item.select_one("span.andes-money-amount__fraction")

        if titulo_tag and precio_tag:
            nombre = titulo_tag.text.strip()
            link = titulo_tag["href"]

            texto = precio_tag.text.replace(".", "").replace(",", ".").strip()
            try:
                precio = float(texto)
                resultados.append({
                    "fuente": "Mercado Libre (FarmaUy)",
                    "producto": nombre,
                    "precio": precio,
                    "url": link
                })
            except ValueError:
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
