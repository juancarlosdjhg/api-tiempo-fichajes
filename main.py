"""
API Start:
uvicorn getRemainingWorkTime:app

Request example:
curl http://127.0.0.1:8000/tiempoFichajes?fichaje1=08:58
"""
import time
from datetime import datetime, timedelta, date
from fastapi import FastAPI
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI()

def convert_timedelta(td):
    return td.seconds // 3600, (td.seconds // 60) % 60, td.seconds % 60

def formatTo2Digits(value):
    return str(value).zfill(2)

class FichajesRequest(BaseModel):
    fichajes: List[str]
    
@app.get("/")
def read_root():
    return {"Hola mundo!"}

@app.get("/tiempoFichajes")
def tiempoFichajes(data: FichajesRequest):
    return readParams(data.fichajes)

def readParams(fichajes: List[str]):
    if not fichajes:
        return {"No hay fichajes"}
    
    ahora = datetime.now().strftime("%H:%M")
    fichajes_times = [datetime.strptime(f, "%H:%M") if f else datetime.strptime(ahora, "%H:%M") for f in fichajes]
    
    tiempo_trabajado = timedelta()
    tiempo_descansos = timedelta()
    
    for i in range(0, len(fichajes_times) - 1, 2):
        tiempo_trabajado += fichajes_times[i + 1] - fichajes_times[i]
        if i + 2 < len(fichajes_times):
            tiempo_descansos += fichajes_times[i + 2] - fichajes_times[i + 1]
    
    work_time = datetime.strptime('06:30' if date.today().month == 8 else '07:30', '%H:%M').time()
    tiempo_salida_estimada = timedelta(hours=work_time.hour, minutes=work_time.minute) + timedelta(hours=fichajes_times[0].hour, minutes=fichajes_times[0].minute) + tiempo_descansos
    
    horas, minutos, _ = convert_timedelta(tiempo_trabajado)
    hora_salida, minuto_salida, _ = convert_timedelta(tiempo_salida_estimada)
    hora_des, minuto_des, _ = convert_timedelta(tiempo_descansos)
    
    if tiempo_trabajado > timedelta(hours=work_time.hour, minutes=work_time.minute):
        tiempo_sobra = tiempo_trabajado - timedelta(hours=work_time.hour, minutes=work_time.minute)
        horas, minutos, _ = convert_timedelta(tiempo_sobra)
        return {
            "Hora de entrada": fichajes_times[0].time(),
            "Tiempo transcurrido": str(tiempo_trabajado).zfill(8),
            "Tiempo descansos": f"{formatTo2Digits(hora_des)}:{formatTo2Digits(minuto_des)}:00",
            "Tiempo restante": "00:00:00",
            "Hora de salida estimada": f"{formatTo2Digits(hora_salida)}:{formatTo2Digits(minuto_salida)}:00",
            "Tiempo sobrante": f"{formatTo2Digits(horas)}:{formatTo2Digits(minutos)}:00"
        }
    else:
        hora_res, minuto_res, _ = convert_timedelta(timedelta(hours=work_time.hour, minutes=work_time.minute) - tiempo_trabajado)
        return {
            "Hora de entrada": fichajes_times[0].time(),
            "Tiempo transcurrido": str(tiempo_trabajado).zfill(8),
            "Tiempo descansos": f"{formatTo2Digits(hora_des)}:{formatTo2Digits(minuto_des)}:00",
            "Tiempo restante": f"{formatTo2Digits(hora_res)}:{formatTo2Digits(minuto_res)}:00",
            "Hora de salida estimada": f"{formatTo2Digits(hora_salida)}:{formatTo2Digits(minuto_salida)}:00"
        }
