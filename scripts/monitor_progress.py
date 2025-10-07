import time
import json
from pathlib import Path

log_file = Path('tests/capitulos/capitulo_61.corrections.jsonl')
prev = 0

print("Monitoreando progreso de corrección...")
print("(Ctrl+C para detener)\n")

for i in range(12):  # 2 minutos de monitoreo
    if not log_file.exists():
        print(f"{i*10}s: Log no existe aún")
    else:
        lines = [l for l in log_file.read_text(encoding='utf-8').splitlines() if l.strip()]
        curr = len(lines)
        status = f"{i*10}s: {curr} correcciones"
        if curr > prev:
            status += f" (+{curr-prev})"
        print(status)
        prev = curr
    time.sleep(10)

print("\nMonitoreo finalizado")
