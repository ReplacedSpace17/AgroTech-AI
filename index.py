from urllib import request
from flask import Flask, jsonify, request
import pandas as pd
import numpy as np
import requests
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor

app = Flask(__name__)

def train_and_predict(json):
    # Cargar los datos de sensores de humedad desde el archivo JSON
    sensor_data = pd.DataFrame(json)


    # Preprocesamiento de datos: transformar y organizar los datos para el entrenamiento del modelo
    X = np.array(sensor_data['valor']).reshape(-1, 1)  # valores de humedad como características
    y = np.arange(len(sensor_data))  # etiquetas de tiempo (índices) como objetivo

    # Dividir los datos en conjuntos de entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Entrenar un modelo de redes neuronales para predecir el tiempo de riego
    model = MLPRegressor(hidden_layer_sizes=(50, 50), max_iter=1000, random_state=42)
    model.fit(X_train, y_train)

    # Hacer una solicitud a la API de clima para obtener datos actuales
    url = 'https://api.weatherapi.com/v1/current.json'
    params = {'key': '22a1123e8d194fd6884104822242504', 'q': 'Mexico City'}  # Reemplaza 'TU_API_KEY' con tu clave de API
    response = requests.get(url, params=params)
    weather_data = response.json()

    # Extraer datos relevantes del clima para determinar el tiempo de riego óptimo
    humidity = weather_data['current']['humidity']

    # Utilizar el modelo entrenado para predecir el tiempo de riego óptimo
    predicted_humidity = model.predict([[humidity]])[0]

    # Función para determinar el tiempo de riego óptimo en base a la predicción de humedad
    def determinar_tiempo_riego(humedad_predicha):
        if humedad_predicha < 40:
            return 45  # minutos
        elif humedad_predicha < 60:
            return 30  # minutos
        else:
            return 15  # minutos

    # Obtener el tiempo de riego óptimo basado en la predicción de humedad
    tiempo_riego_optimo = determinar_tiempo_riego(predicted_humidity)

    # Crear la rutina de riego utilizando los parámetros obtenidos
    activada = tiempo_riego_optimo  # tiempo que la bomba se activa (minutos)
    desactivada = 60 - tiempo_riego_optimo  # tiempo que la bomba se desactiva (minutos)
    ciclo = 3  # veces que se repite la rutina

    rutina_riego = {
        "BID":"4eda315b-5ada-4c52-8901-bcb99cf41027",
        "Activado": activada,
        "Desactivado": desactivada,
        "Ciclos": ciclo
    }

    url = 'http://localhost:3000/agrotech/app/riego'
    try:
    # Realizar la solicitud POST con el objeto rutina_riego en el cuerpo como JSON
        response = requests.post(url, json=rutina_riego)

    # Verificar el estado de la respuesta
        if response.status_code == 200:
            print("Solicitud POST exitosa.")
        else:
            print(f"Error en la solicitud POST: {response.status_code}")

    # Si deseas ver la respuesta del servidor, puedes imprimir el contenido
        print(response.text)

    except Exception as e:
        print(f"Error al realizar la solicitud POST: {str(e)}")

    return rutina_riego


@app.route('/')
def index():
    return "¡Hola, mundo!"

@app.route('/rutina-riego', methods=['GET'])
def get_rutina_riego():
    # Obtener la rutina de riego generada
    rutina = train_and_predict()
    return jsonify(rutina)



@app.route('/CreateRutinaRiego', methods=['POST'])
def receive_json():
    try:
        # Obtener el JSON del cuerpo de la solicitud
        json = request.get_json()

        if json is None:
            raise ValueError("El JSON recibido está vacío o no es válido.")

        # Imprimir el JSON recibido para depuración
        print("JSON recibido:")
        print(json)

        rutina = train_and_predict(json)
        return jsonify(rutina), 200
    except Exception as e:
        # Devolver una respuesta de error con información detallada
        error_message = f"Error al procesar el JSON: {str(e)}"
        return jsonify({'error': error_message}), 400




if __name__ == '__main__':
    # Iniciar el servidor Flask
    app.run(debug=True)

    # Mensaje de confirmación
    print("El servidor Flask está corriendo. Navega a http://127.0.0.1:5000/ en tu navegador.")
