#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(__file__))

from server.db import session_scope
from server.models import User

try:
    with session_scope() as session:
        users = session.query(User).all()
        print(f'Usuarios encontrados: {len(users)}')
        for user in users:
            print(f'  - {user.email} (ID: {user.id})')
        if not users:
            print('No hay usuarios registrados. Crea un usuario primero.')
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
