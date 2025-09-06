from flask import Flask, request, render_template, jsonify
from Bot.Orchestrator import HandleMessage
import json
import os

app = Flask(__name__)

DATES_FILE = "Data/Dates.json"

@app.route("/", methods=["GET", "POST"])
def Home():
    if request.method == "POST":
        user_input = request.form["message"]
        session_id = request.form.get("session_id", "default")
        response = HandleMessage(user_input, session_id=session_id)
        return response  # Devuelve solo la respuesta como texto
    return render_template("Index.html")

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
    app.run(debug=True)




