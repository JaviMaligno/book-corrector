import sys

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv()

# Usar el CLI directamente con importación
sys.argv = [
    "corrector",
    r"tests\capitulos\capitulo 61_corrección.docx",
    "--chunk-words",
    "0",
    "--no-log-docx",
]

from corrector.cli import main

main()
