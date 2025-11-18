#!/usr/bin/env python3

import json

import requests

# Datos del usuario de prueba
user_data = {"email": "demo@example.com", "password": "demo123"}

headers = {"Content-Type": "application/json"}

try:
    # Crear usuario
    response = requests.post(
        "http://localhost:8001/auth/register", data=json.dumps(user_data), headers=headers
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

    if response.status_code == 200:
        print("\n✅ Usuario creado exitosamente!")
        print(f'Email: {user_data["email"]}')
        print(f'Password: {user_data["password"]}')

        # Intentar hacer login para obtener el token
        login_response = requests.post(
            "http://localhost:8001/auth/login", data=json.dumps(user_data), headers=headers
        )

        if login_response.status_code == 200:
            token_data = login_response.json()
            print(f'\n🔑 Token de acceso: {token_data["access_token"]}')
        else:
            print(f"\n❌ Error en login: {login_response.text}")

    else:
        print(f"\n❌ Error creando usuario: {response.text}")

except Exception as e:
    print(f"Error de conexión: {e}")
    print("Asegúrate de que el servidor esté corriendo en http://localhost:8001")
