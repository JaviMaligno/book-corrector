"""
Setup demo data for showcasing the corrector functionality.
Creates sample projects, runs, and correction artifacts.
"""
import os
import json
from pathlib import Path
from sqlmodel import Session, select
from .db import engine
from .models import (
    User, Project, Document, DocumentKind, Run, RunDocument,
    RunDocumentStatus, RunMode, RunStatus, Export, ExportKind,
    Suggestion, SuggestionType, SuggestionSeverity, SuggestionSource, SuggestionStatus
)


SAMPLE_CORRECTIONS = [
    {
        "token_id": 5,
        "line": 1,
        "original": "baca",
        "corrected": "vaca",
        "reason": "Confusión léxica baca/vaca. 'Baca' se refiere al portaequipajes del coche, 'vaca' al animal bovino",
        "context": "La baca mugía en",
        "chunk_index": 0
    },
    {
        "token_id": 18,
        "line": 2,
        "original": "halla",
        "corrected": "haya",
        "reason": "Confusión léxica halla/haya. 'Halla' es del verbo hallar (encontrar), 'haya' del verbo haber o el árbol",
        "context": "espero que halla terminado",
        "chunk_index": 0
    },
    {
        "token_id": 33,
        "line": 3,
        "original": "ojear",
        "corrected": "hojear",
        "reason": "Confusión léxica ojear/hojear. 'Ojear' es mirar, 'hojear' es pasar las páginas de un libro",
        "context": "decidió ojear el libro",
        "chunk_index": 0
    },
    {
        "token_id": 47,
        "line": 4,
        "original": "tubo",
        "corrected": "tuvo",
        "reason": "Confusión léxica tubo/tuvo. 'Tubo' es un cilindro hueco, 'tuvo' es del verbo tener",
        "context": "ella tubo suerte",
        "chunk_index": 0
    },
    {
        "token_id": 62,
        "line": 5,
        "original": "echo",
        "corrected": "hecho",
        "reason": "Confusión léxica echo/hecho. 'Echo' es del verbo echar, 'hecho' es participio de hacer o un suceso",
        "context": "ha echo un trabajo",
        "chunk_index": 0
    },
    {
        "token_id": 78,
        "line": 6,
        "original": "revelar",
        "corrected": "rebelar",
        "reason": "Confusión léxica revelar/rebelar. 'Revelar' es descubrir, 'rebelar' es sublevarse",
        "context": "decidieron revelar contra la injusticia",
        "chunk_index": 0
    },
    {
        "token_id": 94,
        "line": 7,
        "original": "hierba",
        "corrected": "hierva",
        "reason": "Confusión léxica hierba/hierva. 'Hierba' es planta, 'hierva' es del verbo hervir",
        "context": "espera que la hierba el agua",
        "chunk_index": 0
    },
    {
        "token_id": 112,
        "line": 8,
        "original": "ay",
        "corrected": "hay",
        "reason": "Confusión léxica ay/hay. 'Ay' es interjección de dolor, 'hay' del verbo haber",
        "context": "no ay tiempo",
        "chunk_index": 0
    },
    {
        "token_id": 128,
        "line": 9,
        "original": "ablando",
        "corrected": "hablando",
        "reason": "Confusión léxica ablando/hablando. 'Ablando' es del verbo ablandar, 'hablando' del verbo hablar",
        "context": "estaban ablando de política",
        "chunk_index": 0
    },
    {
        "token_id": 145,
        "line": 10,
        "original": "grabe",
        "corrected": "grave",
        "reason": "Confusión léxica grabe/grave. 'Grabe' es del verbo grabar, 'grave' es algo serio",
        "context": "es un problema grabe",
        "chunk_index": 0
    },
    {
        "token_id": 163,
        "line": 11,
        "original": "bello",
        "corrected": "vello",
        "reason": "Confusión léxica bello/vello. 'Bello' es hermoso, 'vello' es pelo fino del cuerpo",
        "context": "el bello corporal",
        "chunk_index": 1
    },
    {
        "token_id": 179,
        "line": 12,
        "original": "a",
        "corrected": "ha",
        "reason": "Confusión léxica a/ha. 'A' es preposición, 'ha' del verbo haber",
        "context": "él a llegado",
        "chunk_index": 1
    },
    {
        "token_id": 195,
        "line": 13,
        "original": "bienes",
        "corrected": "vienes",
        "reason": "Confusión léxica bienes/vienes. 'Bienes' son posesiones, 'vienes' del verbo venir",
        "context": "¿bienes mañana?",
        "chunk_index": 1
    },
    {
        "token_id": 212,
        "line": 14,
        "original": "calló",
        "corrected": "cayó",
        "reason": "Confusión léxica calló/cayó. 'Calló' es del verbo callar, 'cayó' del verbo caer",
        "context": "se calló al suelo",
        "chunk_index": 1
    },
    {
        "token_id": 230,
        "line": 15,
        "original": "sabia",
        "corrected": "sabía",
        "reason": "Error ortográfico: falta tilde en 'sabía' (verbo saber, pretérito imperfecto)",
        "context": "ella sabia la verdad",
        "chunk_index": 1
    }
]


def setup_demo_data():
    """Setup demo data for the application"""
    storage_dir = os.environ.get("STORAGE_DIR", "/data")
    artifacts_dir = Path(storage_dir) / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with Session(engine) as session:
        # Get demo user
        demo_user = session.exec(select(User).where(User.email == "demo@example.com")).first()
        if not demo_user:
            print("⚠️  Demo user not found, skipping demo data setup")
            return

        # Check if demo project already exists
        demo_project = session.exec(
            select(Project).where(
                Project.owner_id == demo_user.id,
                Project.name == "Proyecto Demo"
            )
        ).first()

        if demo_project:
            print("✅ Demo project already exists, skipping")
            return

        # Create demo project
        demo_project = Project(
            owner_id=demo_user.id,
            name="Proyecto Demo",
            lang_variant="es-ES"
        )
        session.add(demo_project)
        session.commit()
        session.refresh(demo_project)
        print(f"✅ Created demo project: {demo_project.id}")

        # Create demo document
        demo_doc = Document(
            project_id=demo_project.id,
            name="documento_ejemplo.docx",
            kind=DocumentKind.docx
        )
        session.add(demo_doc)
        session.commit()
        session.refresh(demo_doc)
        print(f"✅ Created demo document: {demo_doc.id}")

        # Create demo run with specific ID for the frontend URL
        demo_run = Run(
            id="88d6a06f-6179-4979-81eb-b2d573b6c97a",
            project_id=demo_project.id,
            submitted_by=demo_user.id,
            mode=RunMode.profesional,
            status=RunStatus.completed
        )
        session.add(demo_run)

        # Create run document
        run_doc = RunDocument(
            run_id=demo_run.id,
            document_id=demo_doc.id,
            status=RunDocumentStatus.completed,
            use_ai=True
        )
        session.add(run_doc)
        session.commit()
        print(f"✅ Created demo run: {demo_run.id}")

        # Create corrections JSONL file
        corrections_file = artifacts_dir / f"{demo_run.id}_documento_ejemplo.corrections.jsonl"
        with open(corrections_file, "w", encoding="utf-8") as f:
            for correction in SAMPLE_CORRECTIONS:
                f.write(json.dumps(correction, ensure_ascii=False) + "\n")
        print(f"✅ Created corrections file: {corrections_file}")

        # Create export record for corrections
        export_jsonl = Export(
            run_id=demo_run.id,
            kind=ExportKind.jsonl,
            path=str(corrections_file)
        )
        session.add(export_jsonl)

        # Create a summary markdown file
        summary_file = artifacts_dir / f"{demo_run.id}_documento_ejemplo.summary.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(f"""# Resumen de Correcciones - Documento Ejemplo

## Estadísticas

- **Total de correcciones**: {len(SAMPLE_CORRECTIONS)}
- **Confusiones léxicas**: {len([c for c in SAMPLE_CORRECTIONS if 'Confusión léxica' in c['reason']])}
- **Errores ortográficos**: {len([c for c in SAMPLE_CORRECTIONS if 'ortográfico' in c['reason']])}

## Tipos de Errores Encontrados

### Confusiones Léxicas Más Comunes

1. **baca/vaca**: Portaequipajes del coche vs. animal bovino
2. **hojear/ojear**: Pasar páginas vs. mirar
3. **tubo/tuvo**: Cilindro hueco vs. verbo tener
4. **hecho/echo**: Participio de hacer vs. verbo echar

### Recomendaciones

- Revisar el uso de homófonos en contextos específicos
- Prestar atención a las tildes diacríticas (a/ha, tu/tú)
- Verificar la concordancia verbal en tiempos compuestos

---

*Generado automáticamente por el Corrector de Textos*
""")
        print(f"✅ Created summary file: {summary_file}")

        export_md = Export(
            run_id=demo_run.id,
            kind=ExportKind.md,
            path=str(summary_file)
        )
        session.add(export_md)

        # Persist suggestions to database
        print(f"💾 Creating {len(SAMPLE_CORRECTIONS)} suggestions in database...")
        for correction in SAMPLE_CORRECTIONS:
            # Classify suggestion type based on reason
            reason_lower = correction["reason"].lower()
            suggestion_type = SuggestionType.otro
            
            if any(kw in reason_lower for kw in ["ortografía", "ortografia", "spelling"]):
                suggestion_type = SuggestionType.ortografia
            elif any(kw in reason_lower for kw in ["puntuación", "puntuacion", "punctuation"]):
                suggestion_type = SuggestionType.puntuacion
            elif any(kw in reason_lower for kw in ["concordancia", "agreement"]):
                suggestion_type = SuggestionType.concordancia
            elif any(kw in reason_lower for kw in ["estilo", "style"]):
                suggestion_type = SuggestionType.estilo
            elif any(kw in reason_lower for kw in ["léxico", "lexico", "lexical", "confusión", "confusion"]):
                suggestion_type = SuggestionType.lexico
            
            severity = SuggestionSeverity.info
            if "error" in reason_lower:
                severity = SuggestionSeverity.error
            elif "[ELIMINACIÓN]" in correction["reason"]:
                severity = SuggestionSeverity.warning
            
            suggestion = Suggestion(
                run_id=demo_run.id,
                document_id=demo_doc.id,
                token_id=correction["token_id"],
                line=correction["line"],
                suggestion_type=suggestion_type,
                severity=severity,
                before=correction["original"],
                after=correction["corrected"],
                reason=correction["reason"],
                source=SuggestionSource.llm,  # Demo uses AI
                context=correction["context"],
                sentence=None,  # Will be populated by newer runs
                status=SuggestionStatus.pending,  # All demo suggestions start as pending
            )
            session.add(suggestion)

        session.commit()
        print("✅ Demo data setup completed successfully with suggestions")


if __name__ == "__main__":
    setup_demo_data()
