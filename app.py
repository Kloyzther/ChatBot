from flask import Flask, request, render_template, jsonify
from Bot.Orchestrator import HandleMessage
import json
import os

# Crear la app Flask y especificar carpeta de templates
app = Flask(__name__, template_folder="Templates")

# Archivo de datos
DATES_FILE = "Data/Dates.json"

@app.route("/", methods=["GET", "POST"])
def Home():
    if request.method == "POST":
        user_input = request.form.get("message", "")
        session_id = request.form.get("session_id", "default")
        response = HandleMessage(user_input, session_id=session_id)
        return response  # Devuelve solo la respuesta como texto
    return render_template("index.html")  # Asegúrate de que el archivo se llame index.html

# Endpoint para devolver disponibilidad de fechas
@app.route("/api/dates")
def get_dates():
    try:
        with open(DATES_FILE, "r", encoding="utf-8") as f:
            dates = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        dates = {}
    return jsonify(dates)

if __name__ == "__main__":
    # Crear carpeta Data si no existe
    if not os.path.exists("Data"):
        os.makedirs("Data")
    # Crear archivo Dates.json vacío si no existe
    if not os.path.exists(DATES_FILE):
        with open(DATES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
    
    # Ejecutar Flask en host 0.0.0.0 y puerto dinámico para Render
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)






