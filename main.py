"""
API Start:
uvicorn getRemainingWorkTime:app --reload
"""
import time
from datetime import datetime, timedelta, date
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from typing import List, Optional
from pydantic import BaseModel
import pytz
import bcrypt

app = FastAPI()
security = HTTPBasic()

users_db = {
    "user1": {
        "username": "user1",
        "password_hash": b'$2b$12$79K6b9nRrlIuA5l9lsDrLOD53VR8HiDTQ9r8fC9eh0dKAMx7wIsCW'
    }
}

def convert_timedelta(td):
    return td.seconds // 3600, (td.seconds // 60) % 60, td.seconds % 60

def formatTo2Digits(value):
    return str(value).zfill(2)

def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    user = users_db.get(credentials.username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    if not bcrypt.checkpw(credentials.password.encode('utf-8'), user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

class FichajesRequest(BaseModel):
    fichajes: List[str]
    
@app.get("/")
def read_root():
    return {"Hola mundo!"}

@app.get("/tiempoFichajes")
def tiempoFichajes(data: FichajesRequest, username: str = Depends(verify_user)):
    return readParams(sorted(data.fichajes))

def readParams(fichajes: List[str]):
    if not fichajes:
        return {"No hay fichajes"}
    
    print("Hora servidor: ")
    print(datetime.now())

    zona_horaria = pytz.timezone('Atlantic/Canary')
    ahora_dt = datetime.now(zona_horaria)
    
    print("Hora local: ")
    print(ahora_dt)

    ahora = ahora_dt.strftime("%H:%M")
    fichajes_times = [
    zona_horaria.localize(datetime.combine(ahora_dt.date(), datetime.strptime(f, "%H:%M").time()))
    if f else ahora_dt for f in fichajes
]
    
    tiempo_trabajado = timedelta()
    tiempo_descansos = timedelta()
    
    for i in range(0, len(fichajes_times) - 1, 2):
        tiempo_trabajado += fichajes_times[i + 1] - fichajes_times[i]
        if i + 2 < len(fichajes_times):
            tiempo_descansos += fichajes_times[i + 2] - fichajes_times[i + 1]

    # Establecer el tiempo base de trabajo como 7:30 (siempre fijo)
    tiempo_trabajo_base = timedelta(hours=7, minutes=30)

    # Tiempo total que debe transcurrir desde la entrada hasta la salida considerando descansos mínimos de 30 minutos
    descanso_minimo = timedelta(minutes=30)
    tiempo_total_jornada = tiempo_trabajo_base + max(tiempo_descansos, descanso_minimo)

    tiempo_salida_estimada = timedelta(hours=fichajes_times[0].hour, minutes=fichajes_times[0].minute) + tiempo_total_jornada

     # Calcular tiempo transcurrido hasta ahora
    tiempo_trabajado_ahora = timedelta()
    for i in range(0, len(fichajes_times), 2):
        if i + 1 < len(fichajes_times):
            tiempo_trabajado_ahora += fichajes_times[i + 1] - fichajes_times[i]
        else:
            tiempo_trabajado_ahora += ahora_dt - fichajes_times[i]

    horas, minutos, _ = convert_timedelta(tiempo_trabajado)
    hora_salida, minuto_salida, _ = convert_timedelta(tiempo_salida_estimada)
    hora_des, minuto_des, _ = convert_timedelta(tiempo_descansos)
    hora_ahora, minuto_ahora, _ = convert_timedelta(tiempo_trabajado_ahora)

    if tiempo_trabajado > tiempo_trabajo_base:
        tiempo_sobra = tiempo_trabajado - tiempo_trabajo_base
        horas, minutos, _ = convert_timedelta(tiempo_sobra)
        return {
            "Hora de entrada": fichajes_times[0].time(),
            "Tiempo trabajado hasta último fichaje": str(tiempo_trabajado).zfill(8),
            "Tiempo trabajado hasta ahora": f"{formatTo2Digits(hora_ahora)}:{formatTo2Digits(minuto_ahora)}:00",
            "Tiempo descansos": f"{formatTo2Digits(hora_des)}:{formatTo2Digits(minuto_des)}:00",
            "Tiempo restante": "00:00:00",
            "Hora de salida estimada": f"{formatTo2Digits(hora_salida)}:{formatTo2Digits(minuto_salida)}:00",
            "Tiempo sobrante": f"{formatTo2Digits(horas)}:{formatTo2Digits(minutos)}:00"
        }
    else:
        tiempo_restante = tiempo_trabajo_base - tiempo_trabajado
        hora_res, minuto_res, _ = convert_timedelta(tiempo_restante)
        return {
            "Hora de entrada": fichajes_times[0].time(),
            "Tiempo trabajado hasta último fichaje": str(tiempo_trabajado).zfill(8),
            "Tiempo trabajado hasta ahora": f"{formatTo2Digits(hora_ahora)}:{formatTo2Digits(minuto_ahora)}:00",
            "Tiempo descansos": f"{formatTo2Digits(hora_des)}:{formatTo2Digits(minuto_des)}:00",
            "Tiempo restante": f"{formatTo2Digits(hora_res)}:{formatTo2Digits(minuto_res)}:00",
            "Hora de salida estimada": f"{formatTo2Digits(hora_salida)}:{formatTo2Digits(minuto_salida)}:00"
        }
