import json
import os
from datetime import datetime

DOCTORS_FILE = "Data/Doctors.json"
DATES_FILE = "Data/Dates.json"
IDS_FILE = "Data/Ids.json"
APPOINTMENTS_FILE = "Data/Appointments.json"

# Cargar doctores
with open(DOCTORS_FILE, "r", encoding="utf-8") as f:
    doctors_data = json.load(f)

# Cargar fechas ocupadas
if os.path.exists(DATES_FILE):
    with open(DATES_FILE, "r", encoding="utf-8") as f:
        dates_data = json.load(f)
else:
    dates_data = {}

# Cargar IDs y nombres
with open(IDS_FILE, "r", encoding="utf-8") as f:
    ids_data = json.load(f)

# Cargar citas
if os.path.exists(APPOINTMENTS_FILE):
    with open(APPOINTMENTS_FILE, "r", encoding="utf-8") as f:
        appointments_data = json.load(f)
else:
    appointments_data = {"appointments": []}

conversation_state = {}

def save_dates():
    with open(DATES_FILE, "w", encoding="utf-8") as f:
        json.dump(dates_data, f, indent=4, ensure_ascii=False)

def save_appointments():
    with open(APPOINTMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(appointments_data, f, indent=4, ensure_ascii=False)

def HandleMessage(user_input=None, session_id="default", extra=None):
    global conversation_state, dates_data, appointments_data

    if session_id not in conversation_state:
        conversation_state[session_id] = {
            "step": 0,
            "dni": None,
            "nombre": None,
            "celular": None,
            "ciudad": None,
            "action": None,
            "fecha": None,
            "hora": None,
            "doctor": None,
            "cita_antigua": None,
            "citas_usuario": None
        }
    state = conversation_state[session_id]

    if user_input is None:
        return ("¡Hola! Soy tu asistente de doctor 🤖.\n"
                "¿En qué te puedo ayudar?\n"
                "1️⃣ Agendar una nueva cita\n2️⃣ Reagendar una cita existente")

    # Paso 0 -> Paso 1: elegir acción
    if state["step"] == 0:
        state["step"] = 1

    if state["step"] == 1:
        choice = user_input.strip().lower()
        if choice in ["1", "agendar", "nueva cita"]:
            state["step"] = 2
            state["action"] = "agendar"
            return "Perfecto, para agendar una cita necesito tu DNI:"
        elif choice in ["2", "reagendar", "cita existente"]:
            state["step"] = 2
            state["action"] = "reagendar"
            return "Perfecto, para reagendar una cita necesito tu DNI:"
        else:
            return "Por favor elige: 1️⃣ Agendar nueva cita o 2️⃣ Reagendar cita existente"

    # Paso 2: validar DNI
    if state["step"] == 2:
        dni = user_input.strip()
        state["dni"] = dni

        # Buscar en IDS.json
        nombre = ids_data.get(dni)
        if nombre:
            state["nombre"] = nombre
            state["step"] = 3
            return f"Tu nombre es {nombre}. ¿Es correcto? (sí/no)"
        else:
            state["nombre"] = dni
            state["step"] = 3
            return f"No encontré tu nombre. ¿Deseas registrarlo como '{dni}'? (sí/no)"

    # Paso 3: confirmar nombre
    if state["step"] == 3:
        answer = user_input.strip().lower()
        if answer in ["sí", "si", "s"]:
            if state["action"] == "agendar":
                state["step"] = 4
                return "¡Perfecto! Ahora, por favor ingresa tu número de celular:"
            elif state["action"] == "reagendar":
                # Buscar citas del usuario
                citas_usuario = [
                    (i, c) for i, c in enumerate(appointments_data["appointments"]) if c["dni"] == state["dni"]
                ]
                if not citas_usuario:
                    state["step"] = 1
                    return "No tienes citas registradas para reagendar. ¿Deseas agendar una nueva?\n1️⃣ Sí\n2️⃣ No"
                elif len(citas_usuario) == 1:
                    state["cita_antigua"] = citas_usuario[0][1]
                    state["step"] = 6
                    # ➜ Devolver el TEXTO que tu frontend busca para abrir el calendario
                    return "Elige la fecha para tu cita (puedes usar el calendario o escribirla):"
                else:
                    state["step"] = 3.5
                    state["citas_usuario"] = citas_usuario

                    # Agrupar por doctor
                    citas_por_doctor = {}
                    for idx, (i, c) in enumerate(citas_usuario, start=1):
                        doctor = c["doctor"]
                        citas_por_doctor.setdefault(doctor, []).append({
                            "numero": idx,
                            "fecha": c["fecha"],
                            "hora": c["hora"]
                        })

                    # Devolver JSON para frontend
                    return json.dumps({"tipo": "citas", "contenido": citas_por_doctor}, ensure_ascii=False)
        elif answer in ["no", "n"]:
            state["step"] = 2
            state["dni"] = None
            state["nombre"] = None
            return "Entendido. Por favor ingresa nuevamente tu DNI:"
        else:
            return "Por favor responde 'sí' o 'no'."

    # Paso 3.5: elegir cita a reagendar
    if state["step"] == 3.5:
        try:
            choice = int(user_input.strip())
            citas_usuario = state["citas_usuario"]
            if choice < 1 or choice > len(citas_usuario):
                return "Elige un número válido de cita."
            state["cita_antigua"] = citas_usuario[choice - 1][1]
            state["step"] = 6
            # ➜ Devolver el TEXTO que tu frontend busca para abrir el calendario
            return "Elige la fecha para tu cita (puedes usar el calendario o escribirla):"
        except:
            return "Por favor ingresa un número válido."

    # Paso 4: celular (flujo agendar)
    if state["step"] == 4:
        state["celular"] = user_input.strip()
        state["step"] = 5
        return "Gracias. Ahora, por favor indícame tu ciudad:"

    # Paso 5: ciudad (flujo agendar)
    if state["step"] == 5:
        state["ciudad"] = user_input.strip()
        state["step"] = 6
        # ➜ Devolver el TEXTO que tu frontend busca para abrir el calendario (flujo 1 intacto)
        return "Elige la fecha para tu cita (puedes usar el calendario o escribirla):"

    # Paso 6: seleccionar fecha
    if state["step"] == 6:
        try:
            fecha_dt = datetime.strptime(user_input.strip(), "%d/%m/%Y")
            fecha_str = fecha_dt.strftime("%Y-%m-%d")
        except:
            return "Formato de fecha inválido. Usa dd/mm/yyyy."

        state["fecha"] = fecha_str

        # Generar horarios disponibles
        horarios_list = []
        numero = 1
        for doctor, bloques in doctors_data["medicos"].items():
            for bloque in bloques:
                if bloque not in dates_data.get(fecha_str, {}).get(doctor, []):
                    horarios_list.append({
                        "numero": numero,
                        "doctor": doctor,
                        "bloque": bloque
                    })
                    numero += 1

        if not horarios_list:
            return "Lo siento, no hay horarios disponibles para esta fecha. Por favor elige otra fecha."

        state["horarios_map"] = {str(item["numero"]): item for item in horarios_list}
        state["step"] = 7
        return json.dumps({"tipo": "horarios", "contenido": horarios_list}, ensure_ascii=False)

    # Paso 7: elegir horario
    if state["step"] == 7:
        choice = user_input.strip()
        if choice not in state["horarios_map"]:
            return "Por favor elige un número válido."

        seleccion = state["horarios_map"][choice]
        doctor = seleccion["doctor"]
        bloque = seleccion["bloque"]
        fecha = state["fecha"]

        # Si es reagendar → eliminar cita anterior
        if state["action"] == "reagendar" and state["cita_antigua"]:
            cita_antigua = state["cita_antigua"]
            appointments_data["appointments"] = [
                c for c in appointments_data["appointments"] if c != cita_antigua
            ]
            fecha_ant = datetime.strptime(cita_antigua["fecha"], "%d/%m/%Y").strftime("%Y-%m-%d")
            if fecha_ant in dates_data and cita_antigua["doctor"] in dates_data[fecha_ant]:
                if cita_antigua["hora"] in dates_data[fecha_ant][cita_antigua["doctor"]]:
                    dates_data[fecha_ant][cita_antigua["doctor"]].remove(cita_antigua["hora"])
            save_dates()
            save_appointments()

        # Guardar en dates_data
        if fecha not in dates_data:
            dates_data[fecha] = {doc: [] for doc in doctors_data["medicos"].keys()}
        dates_data[fecha][doctor].append(bloque)
        save_dates()

        # Guardar cita en Appointments.json
        nueva_cita = {
            "paciente": state["nombre"],
            "dni": state["dni"],
            "doctor": doctor,
            "fecha": datetime.strptime(fecha, "%Y-%m-%d").strftime("%d/%m/%Y"),
            "hora": bloque,
            "celular": state.get("celular"),
            "ciudad": state.get("ciudad")
        }
        appointments_data["appointments"].append(nueva_cita)
        save_appointments()

        # Resetear estado
        state["doctor"] = doctor
        state["hora"] = bloque
        state["cita_antigua"] = None
        state["citas_usuario"] = None
        state["step"] = 1

        # Mensaje final detallado
        return (f"✅ Cita {'reagendada' if state['action']=='reagendar' else 'agendada'} con éxito:\n\n"
                f"Paciente: {nueva_cita['paciente']}\n"
                f"DNI: {nueva_cita['dni']}\n"
                f"Doctor: {nueva_cita['doctor']}\n"
                f"Fecha: {nueva_cita['fecha']}\n"
                f"Hora: {nueva_cita['hora']}\n"
                f"Celular: {nueva_cita.get('celular','No registrado')}\n"
                f"Ciudad: {nueva_cita.get('ciudad','No registrada')}\n\n"
                "¿Deseas hacer otra acción?\n1️⃣ Agendar nueva cita\n2️⃣ Reagendar cita existente")
















