#!/usr/bin/env python3
"""
Migration script: Render Postgres -> Neon Postgres
Zero-downtime migration for corrector database
"""

import os
import sys

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# Load environment variables
load_dotenv()

# Neon connection string from environment
NEON_DATABASE_URL = os.getenv("NEON_DATABASE_URL")
if not NEON_DATABASE_URL:
    print("ERROR: NEON_DATABASE_URL not set in environment")
    sys.exit(1)

# SQL to create enum types
ENUM_TYPES = """
-- Document types
DO $$ BEGIN
    CREATE TYPE documentkind AS ENUM ('docx', 'txt', 'md');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE documentstatus AS ENUM ('new', 'queued', 'processing', 'ready');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Export types
DO $$ BEGIN
    CREATE TYPE exportkind AS ENUM ('docx', 'csv', 'jsonl', 'md');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- User roles
DO $$ BEGIN
    CREATE TYPE role AS ENUM ('free', 'premium', 'admin');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Run types
DO $$ BEGIN
    CREATE TYPE rundocumentstatus AS ENUM ('queued', 'processing', 'completed', 'failed');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE runmode AS ENUM ('rapido', 'profesional');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE runstatus AS ENUM ('queued', 'processing', 'exporting', 'completed', 'failed', 'canceled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Suggestion types
DO $$ BEGIN
    CREATE TYPE suggestionseverity AS ENUM ('error', 'warning', 'info');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE suggestionsource AS ENUM ('rule', 'llm');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE suggestionstatus AS ENUM ('pending', 'accepted', 'rejected');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE suggestiontype AS ENUM ('ortografia', 'puntuacion', 'concordancia', 'estilo', 'lexico', 'otro');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
"""

# SQL to create tables
CREATE_TABLES = """
-- User table
CREATE TABLE IF NOT EXISTS "user" (
    id VARCHAR NOT NULL PRIMARY KEY,
    email VARCHAR NOT NULL,
    password_hash VARCHAR NOT NULL,
    role role NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- Project table
CREATE TABLE IF NOT EXISTS project (
    id VARCHAR NOT NULL PRIMARY KEY,
    owner_id VARCHAR NOT NULL REFERENCES "user"(id),
    name VARCHAR NOT NULL,
    lang_variant VARCHAR,
    style_profile_id VARCHAR,
    config_json VARCHAR,
    created_at TIMESTAMP NOT NULL
);

-- Document table
CREATE TABLE IF NOT EXISTS document (
    id VARCHAR NOT NULL PRIMARY KEY,
    project_id VARCHAR NOT NULL REFERENCES project(id),
    name VARCHAR NOT NULL,
    path VARCHAR,
    kind documentkind NOT NULL,
    checksum VARCHAR,
    status documentstatus NOT NULL,
    content_backup TEXT
);

-- Run table
CREATE TABLE IF NOT EXISTS run (
    id VARCHAR NOT NULL PRIMARY KEY,
    project_id VARCHAR NOT NULL REFERENCES project(id),
    submitted_by VARCHAR NOT NULL REFERENCES "user"(id),
    mode runmode NOT NULL,
    status runstatus NOT NULL,
    params_json VARCHAR,
    created_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);

-- RunDocument table
CREATE TABLE IF NOT EXISTS rundocument (
    id VARCHAR NOT NULL PRIMARY KEY,
    run_id VARCHAR NOT NULL REFERENCES run(id),
    document_id VARCHAR NOT NULL REFERENCES document(id),
    status rundocumentstatus NOT NULL,
    use_ai BOOLEAN NOT NULL,
    locked_by VARCHAR,
    locked_at TIMESTAMP,
    heartbeat_at TIMESTAMP,
    attempt_count INTEGER NOT NULL,
    last_error VARCHAR
);

-- Export table
CREATE TABLE IF NOT EXISTS export (
    id VARCHAR NOT NULL PRIMARY KEY,
    run_id VARCHAR NOT NULL REFERENCES run(id),
    kind exportkind NOT NULL,
    path VARCHAR NOT NULL
);

-- NormativeCatalog table
CREATE TABLE IF NOT EXISTS normativecatalog (
    id VARCHAR NOT NULL PRIMARY KEY,
    source VARCHAR NOT NULL,
    ref VARCHAR NOT NULL,
    title VARCHAR,
    snippet VARCHAR
);

-- Suggestion table
CREATE TABLE IF NOT EXISTS suggestion (
    id VARCHAR NOT NULL PRIMARY KEY,
    run_id VARCHAR NOT NULL REFERENCES run(id),
    document_id VARCHAR NOT NULL REFERENCES document(id),
    token_id INTEGER NOT NULL,
    line INTEGER NOT NULL,
    location VARCHAR,
    suggestion_type suggestiontype NOT NULL,
    severity suggestionseverity NOT NULL,
    before VARCHAR NOT NULL,
    after VARCHAR NOT NULL,
    reason VARCHAR NOT NULL,
    citation_id VARCHAR REFERENCES normativecatalog(id),
    source suggestionsource NOT NULL,
    confidence DOUBLE PRECISION,
    context VARCHAR,
    sentence VARCHAR,
    status suggestionstatus NOT NULL,
    created_at TIMESTAMP NOT NULL
);

-- StyleProfile table
CREATE TABLE IF NOT EXISTS styleprofile (
    id VARCHAR NOT NULL PRIMARY KEY,
    project_id VARCHAR NOT NULL REFERENCES project(id),
    derived_from_run_id VARCHAR REFERENCES run(id),
    data_json VARCHAR,
    era VARCHAR,
    region VARCHAR,
    treatment VARCHAR,
    quotes_style VARCHAR,
    numeric_style VARCHAR,
    leismo BOOLEAN,
    solo_tilde BOOLEAN,
    persona_rules VARCHAR
);

-- Add FK for project.style_profile_id after styleprofile exists
DO $$ BEGIN
    ALTER TABLE project ADD CONSTRAINT project_style_profile_id_fkey
    FOREIGN KEY (style_profile_id) REFERENCES styleprofile(id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Character table
CREATE TABLE IF NOT EXISTS "character" (
    id VARCHAR NOT NULL PRIMARY KEY,
    project_id VARCHAR NOT NULL REFERENCES project(id),
    name VARCHAR NOT NULL,
    traits_json VARCHAR
);

-- GlossaryTerm table
CREATE TABLE IF NOT EXISTS glossaryterm (
    id VARCHAR NOT NULL PRIMARY KEY,
    project_id VARCHAR NOT NULL REFERENCES project(id),
    term VARCHAR NOT NULL,
    preferred VARCHAR,
    notes VARCHAR
);

-- UsageLog table
CREATE TABLE IF NOT EXISTS usagelog (
    id VARCHAR NOT NULL PRIMARY KEY,
    user_id VARCHAR NOT NULL REFERENCES "user"(id),
    metric VARCHAR NOT NULL,
    amount INTEGER NOT NULL,
    at TIMESTAMP NOT NULL
);
"""

# Data to insert
USER_DATA = [
    (
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "demo@example.com",
        "$2b$12$ke80q1AHic3PCdQQtm6/0uf3Ym32EAkeUMO6fnh/Z83vl/3j0QisS",
        "premium",
        "2025-11-15T14:28:59.429742",
    )
]

PROJECT_DATA = [
    (
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "Proyecto Demo",
        "es-ES",
        None,
        None,
        "2025-11-15T14:28:59.52963",
    )
]

DOCUMENT_DATA = [
    (
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "documento_ejemplo.docx",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/documents/documento_ejemplo.docx",
        "docx",
        None,
        "new",
        "La baca mugía en el prado.\nespero que halla terminado el trabajo.\ndecidió ojear el libro en la biblioteca.\nella tubo suerte en el concurso.\nha echo un trabajo excelente.\ndecidieron revelar contra la injusticia.\nespera que la hierba el agua.\nno ay tiempo para perder.\nestaban ablando de política.\nes un problema grabe.\nel bello corporal es natural.\nél a llegado temprano.\n¿bienes mañana?\nse calló al suelo.\nella sabia la verdad.",
    ),
    (
        "caaebe26-2746-40e8-976b-0d15ee3ac8be",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/documents/7ddfd025-3659-4aee-aef3-e69059248f5c",
        "docx",
        None,
        "new",
        "La baca mugía en el prado.\nespero que halla terminado el trabajo.\ndecidió ojear el libro en la biblioteca.\nella tubo suerte en el concurso.\nha echo un trabajo excelente.\ndecidieron revelar contra la injusticia.\nespera que la hierba el agua.\nno ay tiempo para perder.\nestaban ablando de política.\nes un problema grabe.\nel bello corporal es natural.\nél a llegado temprano.\n¿bienes mañana?\nse calló al suelo.\nella sabia la verdad.",
    ),
]

RUN_DATA = [
    (
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "profesional",
        "completed",
        None,
        "2025-11-15T14:28:59.819527",
        None,
        None,
    ),
    (
        "3cd4082f-0563-4f19-88d0-c21c177ca6ab",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "failed",
        '{"use_ai": false}',
        "2025-11-15T14:42:57.360023",
        None,
        None,
    ),
    (
        "27b1e042-3d99-4db9-ba59-5091b2752c1f",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "failed",
        '{"use_ai": false}',
        "2025-11-15T14:43:18.069749",
        None,
        None,
    ),
    (
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "completed",
        '{"use_ai": false}',
        "2025-11-15T15:47:32.63931",
        None,
        None,
    ),
    (
        "3216ab44-171d-4163-a552-ac6cad5faf96",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "failed",
        '{"use_ai": true}',
        "2025-11-15T15:51:54.9768",
        None,
        None,
    ),
    (
        "473c0601-2a21-46fb-80d3-99f6dab637fc",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "failed",
        '{"use_ai": true}',
        "2025-11-15T16:07:30.553544",
        None,
        None,
    ),
    (
        "c5c79138-a13a-4a44-b804-0925a39f786e",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "failed",
        '{"use_ai": true}',
        "2025-11-15T16:28:28.055818",
        None,
        None,
    ),
    (
        "d751913c-1f08-4e95-8e36-51f2acea2687",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "rapido",
        "queued",
        '{"use_ai": true}',
        "2025-11-15T16:48:52.185727",
        None,
        None,
    ),
    (
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "700b8408-eb29-4684-978b-4c7a76f6d3c6",
        "5029e455-58a2-4d8d-bdaa-ffcd9487d120",
        "profesional",
        "failed",
        '{"use_ai": true}',
        "2025-11-17T12:41:34.64324",
        None,
        None,
    ),
]

RUNDOCUMENT_DATA = [
    (
        "c553599e-2c91-4f38-aaad-1a023cb646d8",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "completed",
        True,
        None,
        None,
        None,
        0,
        None,
    ),
    (
        "94cb2a3b-2812-41c0-bc6c-1d00bfc117c7",
        "3cd4082f-0563-4f19-88d0-c21c177ca6ab",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "failed",
        False,
        None,
        None,
        None,
        1,
        "document not found",
    ),
    (
        "549e4f2d-4f88-4ff4-8fdb-8298fa8e348f",
        "27b1e042-3d99-4db9-ba59-5091b2752c1f",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "failed",
        False,
        None,
        None,
        None,
        1,
        "document not found",
    ),
    (
        "37e9c265-b86c-4906-b681-b143d349ac16",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "completed",
        False,
        "b3725eec-c415-4423-8167-ffd4802e2d05",
        "2025-11-15T15:47:33.1035",
        None,
        1,
        None,
    ),
    (
        "8b196897-0fe8-4df4-90a0-e1c927481fd4",
        "3216ab44-171d-4163-a552-ac6cad5faf96",
        "caaebe26-2746-40e8-976b-0d15ee3ac8be",
        "failed",
        True,
        None,
        None,
        None,
        1,
        "missing document path",
    ),
    (
        "821a9e01-9b85-40af-b176-b7ad7e20526b",
        "473c0601-2a21-46fb-80d3-99f6dab637fc",
        "caaebe26-2746-40e8-976b-0d15ee3ac8be",
        "failed",
        True,
        None,
        None,
        None,
        1,
        "missing document path",
    ),
    (
        "b49491dc-8ff8-4763-833c-ea7019da27f8",
        "c5c79138-a13a-4a44-b804-0925a39f786e",
        "caaebe26-2746-40e8-976b-0d15ee3ac8be",
        "failed",
        True,
        None,
        None,
        None,
        1,
        "missing document path",
    ),
    (
        "db939d90-ed9b-43c0-bbd6-d77da363aee8",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "caaebe26-2746-40e8-976b-0d15ee3ac8be",
        "failed",
        True,
        None,
        None,
        None,
        1,
        "missing document path",
    ),
    (
        "ad746265-0cbf-45ec-928f-359b34369f0d",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        "completed",
        True,
        "6a659423-6614-4b90-ae8d-2a0d9d0a381c",
        "2025-11-17T12:41:34.741674",
        None,
        1,
        None,
    ),
]

EXPORT_DATA = [
    (
        "d53536f0-40ff-46a7-b4ac-79181d4c8edb",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "jsonl",
        "/tmp/artifacts/88d6a06f-6179-4979-81eb-b2d573b6c97a_documento_ejemplo.corrections.jsonl",
    ),
    (
        "81fd5a96-4394-4989-981d-58bfaf6bf0b1",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "md",
        "/tmp/artifacts/88d6a06f-6179-4979-81eb-b2d573b6c97a_documento_ejemplo.summary.md",
    ),
    (
        "80b06192-ab8e-4428-a1df-0041a1b0903c",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "docx",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/63ff8ad5-fc5d-4946-ae14-42f9df6e6e90/documento_ejemplo.corrected.docx",
    ),
    (
        "3b5ab2d3-02a0-4306-845d-f470ef4e797f",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "jsonl",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/63ff8ad5-fc5d-4946-ae14-42f9df6e6e90/documento_ejemplo.corrections.jsonl",
    ),
    (
        "b78dd863-de19-49a5-bfc8-d183e19a5e23",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "docx",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/63ff8ad5-fc5d-4946-ae14-42f9df6e6e90/documento_ejemplo.corrections.docx",
    ),
    (
        "1a4267f4-5bb5-49c9-ba19-1a80fef88dc2",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "csv",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/63ff8ad5-fc5d-4946-ae14-42f9df6e6e90/documento_ejemplo.changelog.csv",
    ),
    (
        "83d909b5-870b-40b0-be14-132a45b7b34e",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "md",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/63ff8ad5-fc5d-4946-ae14-42f9df6e6e90/documento_ejemplo.summary.md",
    ),
    (
        "9d465a4d-dee6-4854-8096-309a964685ab",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "docx",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/a4c92c2a-bf54-4329-8d50-323ecd2611d8/documento_ejemplo.corrected.docx",
    ),
    (
        "07ce39d2-5ef3-42bc-8aba-48ad1622f007",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "jsonl",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/a4c92c2a-bf54-4329-8d50-323ecd2611d8/documento_ejemplo.corrections.jsonl",
    ),
    (
        "de3b91bc-92ad-46a9-93ce-38aeb0855adb",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "docx",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/a4c92c2a-bf54-4329-8d50-323ecd2611d8/documento_ejemplo.corrections.docx",
    ),
    (
        "cf31b670-2442-4aa2-89e5-6ee46a90ea94",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "csv",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/a4c92c2a-bf54-4329-8d50-323ecd2611d8/documento_ejemplo.changelog.csv",
    ),
    (
        "e6945751-35cd-4b33-89ce-d92e027daf75",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "md",
        "/tmp/5029e455-58a2-4d8d-bdaa-ffcd9487d120/700b8408-eb29-4684-978b-4c7a76f6d3c6/runs/a4c92c2a-bf54-4329-8d50-323ecd2611d8/documento_ejemplo.summary.md",
    ),
]

SUGGESTION_DATA = [
    (
        "0503bbcf-f041-4c3d-ae90-f21e8c950236",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        2,
        1,
        None,
        "lexico",
        "info",
        "baca",
        "vaca",
        "Confusión léxica baca/vaca. 'Baca' se refiere al portaequipajes del coche, 'vaca' al animal bovino",
        None,
        "llm",
        None,
        "La baca mugía en",
        None,
        "pending",
        "2025-11-15T14:28:59.930509",
    ),
    (
        "40054b50-943a-43a4-8213-b2e9c1fa8c76",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        17,
        2,
        None,
        "lexico",
        "info",
        "halla",
        "haya",
        "Confusión léxica halla/haya. 'Halla' es del verbo hallar (encontrar), 'haya' del verbo haber o el árbol",
        None,
        "llm",
        None,
        "espero que halla terminado",
        None,
        "pending",
        "2025-11-15T14:28:59.931013",
    ),
    (
        "f8605402-8f1e-4aa1-b23d-f56844ceef23",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        28,
        3,
        None,
        "lexico",
        "info",
        "ojear",
        "hojear",
        "Confusión léxica ojear/hojear. 'Ojear' es mirar, 'hojear' es pasar las páginas de un libro",
        None,
        "llm",
        None,
        "decidió ojear el libro",
        None,
        "pending",
        "2025-11-15T14:28:59.931215",
    ),
    (
        "c141136e-dcf1-470a-b7d2-40110ba2025a",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        43,
        4,
        None,
        "lexico",
        "info",
        "tubo",
        "tuvo",
        "Confusión léxica tubo/tuvo. 'Tubo' es un cilindro hueco, 'tuvo' es del verbo tener",
        None,
        "llm",
        None,
        "ella tubo suerte",
        None,
        "pending",
        "2025-11-15T14:28:59.9314",
    ),
    (
        "412e4351-ca32-458f-a75b-1bfe7eb8eaa5",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        56,
        5,
        None,
        "lexico",
        "info",
        "echo",
        "hecho",
        "Confusión léxica echo/hecho. 'Echo' es del verbo echar, 'hecho' es participio de hacer o un suceso",
        None,
        "llm",
        None,
        "ha echo un trabajo",
        None,
        "pending",
        "2025-11-15T14:28:59.931581",
    ),
    (
        "03c002b6-5967-494e-983e-01dc927d9df2",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        67,
        6,
        None,
        "lexico",
        "info",
        "revelar",
        "rebelar",
        "Confusión léxica revelar/rebelar. 'Revelar' es descubrir, 'rebelar' es sublevarse",
        None,
        "llm",
        None,
        "decidieron revelar contra la injusticia",
        None,
        "pending",
        "2025-11-15T14:28:59.931792",
    ),
    (
        "648d6856-63e3-4cb3-b4be-7a54324db8f0",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        82,
        7,
        None,
        "lexico",
        "info",
        "hierba",
        "hierva",
        "Confusión léxica hierba/hierva. 'Hierba' es planta, 'hierva' es del verbo hervir",
        None,
        "llm",
        None,
        "espera que la hierba el agua",
        None,
        "pending",
        "2025-11-15T14:28:59.931973",
    ),
    (
        "a7d9f986-b11c-4896-a2a4-4a079b596804",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        91,
        8,
        None,
        "lexico",
        "info",
        "ay",
        "hay",
        "Confusión léxica ay/hay. 'Ay' es interjección de dolor, 'hay' del verbo haber",
        None,
        "llm",
        None,
        "no ay tiempo",
        None,
        "pending",
        "2025-11-15T14:28:59.932149",
    ),
    (
        "19fce0ca-ea28-4288-8c12-e63cf49ea63d",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        102,
        9,
        None,
        "lexico",
        "info",
        "ablando",
        "hablando",
        "Confusión léxica ablando/hablando. 'Ablando' es del verbo ablandar, 'hablando' del verbo hablar",
        None,
        "llm",
        None,
        "estaban ablando de política",
        None,
        "pending",
        "2025-11-15T14:28:59.932321",
    ),
    (
        "996c7780-4aa2-4af3-b821-3a41e69ab770",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        115,
        10,
        None,
        "lexico",
        "info",
        "grabe",
        "grave",
        "Confusión léxica grabe/grave. 'Grabe' es del verbo grabar, 'grave' es algo serio",
        None,
        "llm",
        None,
        "es un problema grabe",
        None,
        "pending",
        "2025-11-15T14:28:59.932489",
    ),
    (
        "cfa6adb4-bfd0-4ef7-9463-45ab79167387",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        120,
        11,
        None,
        "lexico",
        "info",
        "bello",
        "vello",
        "Confusión léxica bello/vello. 'Bello' es hermoso, 'vello' es pelo fino del cuerpo",
        None,
        "llm",
        None,
        "el bello corporal",
        None,
        "pending",
        "2025-11-15T14:28:59.932657",
    ),
    (
        "db2d0336-f493-4e7d-8bdb-0e50244a952a",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        131,
        12,
        None,
        "lexico",
        "info",
        "a",
        "ha",
        "Confusión léxica a/ha. 'A' es preposición, 'ha' del verbo haber",
        None,
        "llm",
        None,
        "él a llegado",
        None,
        "pending",
        "2025-11-15T14:28:59.93286",
    ),
    (
        "aebb0934-e9e8-4acb-b9f1-fb9759a24c5a",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        139,
        13,
        None,
        "lexico",
        "info",
        "bienes",
        "vienes",
        "Confusión léxica bienes/vienes. 'Bienes' son posesiones, 'vienes' del verbo venir",
        None,
        "llm",
        None,
        "¿bienes mañana?",
        None,
        "pending",
        "2025-11-15T14:28:59.933034",
    ),
    (
        "7aaf3cad-7227-4cfd-947b-945e42891dd5",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        146,
        14,
        None,
        "lexico",
        "info",
        "calló",
        "cayó",
        "Confusión léxica calló/cayó. 'Calló' es del verbo callar, 'cayó' del verbo caer",
        None,
        "llm",
        None,
        "se calló al suelo",
        None,
        "pending",
        "2025-11-15T14:28:59.933213",
    ),
    (
        "1937fd6e-7d65-405f-aa69-340321e1c244",
        "88d6a06f-6179-4979-81eb-b2d573b6c97a",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        155,
        15,
        None,
        "otro",
        "error",
        "sabia",
        "sabía",
        "Error ortográfico: falta tilde en 'sabía' (verbo saber, pretérito imperfecto)",
        None,
        "llm",
        None,
        "ella sabia la verdad",
        None,
        "pending",
        "2025-11-15T14:28:59.933387",
    ),
    (
        "145bf1a9-598a-4530-a299-0c767731409d",
        "63ff8ad5-fc5d-4946-ae14-42f9df6e6e90",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        28,
        3,
        None,
        "lexico",
        "info",
        "ojear",
        "hojear",
        "Confusión ojear/hojear (pasar páginas)",
        None,
        "rule",
        None,
        "decidió ojear el",
        "decidió ojear el libro en la biblioteca.",
        "pending",
        "2025-11-15T15:47:33.173324",
    ),
    (
        "41142a4b-64db-40c9-abd4-883a6d597e75",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        102,
        9,
        None,
        "lexico",
        "info",
        "ablando",
        "hablando",
        "Confusión entre 'ablando' (del verbo ablandar) y 'hablando' (del verbo hablar).",
        None,
        "llm",
        None,
        "estaban ablando de",
        "estaban ablando de política.",
        "accepted",
        "2025-11-17T12:42:03.724178",
    ),
    (
        "5659ef41-fce8-4dde-b720-b520bff47ae0",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        43,
        4,
        None,
        "lexico",
        "info",
        "tubo",
        "tuvo",
        "Confusión entre 'tubo' (sustantivo) y 'tuvo' (verbo tener en pasado).",
        None,
        "llm",
        None,
        "ella tubo suerte",
        "ella tubo suerte en el concurso.",
        "accepted",
        "2025-11-17T12:42:03.723531",
    ),
    (
        "5f889020-41f6-4706-a226-37c6f1ecfeb5",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        28,
        3,
        None,
        "lexico",
        "info",
        "ojear",
        "hojear",
        "Confusión entre 'ojear' (mirar rápidamente) y 'hojear' (pasar las hojas de un libro). El contexto de un libro en una biblioteca sugiere 'hojear'.",
        None,
        "llm",
        None,
        "decidió ojear el",
        "decidió ojear el libro en la biblioteca.",
        "accepted",
        "2025-11-17T12:42:03.723399",
    ),
    (
        "659cc207-5652-4d8d-a4f0-e81c1b11e897",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        131,
        12,
        None,
        "lexico",
        "info",
        "a",
        "ha",
        "Confusión entre 'a' (preposición) y 'ha' (verbo haber para formar tiempos compuestos).",
        None,
        "llm",
        None,
        "él a llegado",
        "él a llegado temprano.",
        "accepted",
        "2025-11-17T12:42:03.724492",
    ),
    (
        "6f9940c5-a5ea-4298-8392-e0000e4c6ec5",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        155,
        15,
        None,
        "lexico",
        "info",
        "sabia",
        "sabía",
        "Confusión entre 'sabia' (adjetivo/sustantivo) y 'sabía' (verbo saber en pretérito imperfecto).",
        None,
        "llm",
        None,
        "ella sabia la",
        "ella sabia la verdad.",
        "accepted",
        "2025-11-17T12:42:03.724798",
    ),
    (
        "88f282b0-47b9-4143-bc5b-ceb55d4eb018",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        91,
        8,
        None,
        "lexico",
        "info",
        "ay",
        "hay",
        "Confusión entre 'ay' (interjección) y 'hay' (verbo haber en tercera persona del singular).",
        None,
        "llm",
        None,
        "no ay tiempo",
        "no ay tiempo para perder.",
        "accepted",
        "2025-11-17T12:42:03.72407",
    ),
    (
        "9b0ef301-cd44-4eab-af38-c0e87eccc9f7",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        146,
        14,
        None,
        "lexico",
        "info",
        "calló",
        "cayó",
        "Confusión entre 'calló' (del verbo callar) y 'cayó' (del verbo caer).",
        None,
        "llm",
        None,
        "se calló al",
        "se calló al suelo.",
        "accepted",
        "2025-11-17T12:42:03.724698",
    ),
    (
        "d8daee86-6255-4d8e-9c32-39de07288765",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        115,
        10,
        None,
        "lexico",
        "info",
        "grabe",
        "grave",
        "Confusión entre 'grabe' (verbo grabar/gravar) y 'grave' (adjetivo, serio).",
        None,
        "llm",
        None,
        "problema grabe.\nel",
        "es un problema grabe.",
        "accepted",
        "2025-11-17T12:42:03.724282",
    ),
    (
        "db7ba023-b61a-42b5-85a4-60c2f1ba6b58",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        82,
        7,
        None,
        "lexico",
        "info",
        "hierba",
        "hierva",
        "Confusión entre 'hierba' (sustantivo, planta) y 'hierva' (verbo hervir en subjuntivo). El contexto sugiere 'Esperar que el agua hierva'.",
        None,
        "llm",
        None,
        "la hierba el",
        "espera que la hierba el agua.",
        "accepted",
        "2025-11-17T12:42:03.723948",
    ),
    (
        "e044fba2-6045-4cb3-86a6-1aee9f95daef",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        2,
        1,
        None,
        "lexico",
        "info",
        "baca",
        "vaca",
        "Confusión entre 'baca' (portaequipajes) y 'vaca' (animal bovino). El contexto de 'mugía' indica 'vaca'.",
        None,
        "llm",
        None,
        "La baca mugía",
        "La baca mugía en el prado.",
        "accepted",
        "2025-11-17T12:42:03.722925",
    ),
    (
        "e0643dd9-dc99-4f68-aa78-a041a474d417",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        17,
        2,
        None,
        "lexico",
        "info",
        "halla",
        "haya",
        "Confusión entre 'halla' (del verbo hallar) y 'haya' (del verbo haber, para formar tiempos compuestos).",
        None,
        "llm",
        None,
        "que halla terminado",
        "espero que halla terminado el trabajo.",
        "accepted",
        "2025-11-17T12:42:03.723236",
    ),
    (
        "e1c02cdb-7fd6-40e1-809f-bde61452e638",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        56,
        5,
        None,
        "lexico",
        "info",
        "echo",
        "hecho",
        "Confusión entre 'echo' (del verbo echar) y 'hecho' (participio del verbo hacer). 'Ha hecho' es la forma correcta para formar el pretérito perfecto compuesto.",
        None,
        "llm",
        None,
        "ha echo un",
        "ha echo un trabajo excelente.",
        "accepted",
        "2025-11-17T12:42:03.723653",
    ),
    (
        "e8594a72-4d2e-486c-ae33-4dc82da65584",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        120,
        11,
        None,
        "lexico",
        "info",
        "bello",
        "vello",
        "Confusión entre 'bello' (adjetivo, hermoso) y 'vello' (sustantivo, pelo corporal).",
        None,
        "llm",
        None,
        "el bello corporal",
        "el bello corporal es natural.",
        "accepted",
        "2025-11-17T12:42:03.724383",
    ),
    (
        "f3ac95a5-be4b-4062-8d89-876382586bd8",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        67,
        6,
        None,
        "lexico",
        "info",
        "revelar",
        "rebelar",
        "Confusión entre 'revelar' (descubrir, mostrar) y 'rebelar' (levantarse contra una autoridad o sistema).",
        None,
        "llm",
        None,
        "decidieron revelar contra",
        "decidieron revelar contra la injusticia.",
        "accepted",
        "2025-11-17T12:42:03.723769",
    ),
    (
        "f5d0be58-8b66-4a06-8f5d-2c92d035beb5",
        "a4c92c2a-bf54-4329-8d50-323ecd2611d8",
        "7ddfd025-3659-4aee-aef3-e69059248f5c",
        139,
        13,
        None,
        "lexico",
        "info",
        "bienes",
        "vienes",
        "Confusión entre 'bienes' (sustantivo, posesiones) y 'vienes' (verbo venir).",
        None,
        "llm",
        None,
        ".\n¿bienes mañana?",
        "¿bienes mañana?",
        "accepted",
        "2025-11-17T12:42:03.724596",
    ),
]


def migrate():
    """Run the migration from Render to Neon"""
    print("Connecting to Neon Postgres...")

    try:
        conn = psycopg2.connect(NEON_DATABASE_URL)
        conn.autocommit = False
        cur = conn.cursor()

        print("Creating enum types...")
        cur.execute(ENUM_TYPES)

        print("Creating tables...")
        cur.execute(CREATE_TABLES)

        print("Inserting users...")
        execute_values(
            cur,
            """
            INSERT INTO "user" (id, email, password_hash, role, created_at)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            USER_DATA,
        )

        print("Inserting projects...")
        execute_values(
            cur,
            """
            INSERT INTO project (id, owner_id, name, lang_variant, style_profile_id, config_json, created_at)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            PROJECT_DATA,
        )

        print("Inserting documents...")
        execute_values(
            cur,
            """
            INSERT INTO document (id, project_id, name, path, kind, checksum, status, content_backup)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            DOCUMENT_DATA,
        )

        print("Inserting runs...")
        execute_values(
            cur,
            """
            INSERT INTO run (id, project_id, submitted_by, mode, status, params_json, created_at, started_at, finished_at)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            RUN_DATA,
        )

        print("Inserting rundocuments...")
        execute_values(
            cur,
            """
            INSERT INTO rundocument (id, run_id, document_id, status, use_ai, locked_by, locked_at, heartbeat_at, attempt_count, last_error)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            RUNDOCUMENT_DATA,
        )

        print("Inserting exports...")
        execute_values(
            cur,
            """
            INSERT INTO export (id, run_id, kind, path)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            EXPORT_DATA,
        )

        print("Inserting suggestions...")
        execute_values(
            cur,
            """
            INSERT INTO suggestion (id, run_id, document_id, token_id, line, location, suggestion_type, severity, before, after, reason, citation_id, source, confidence, context, sentence, status, created_at)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """,
            SUGGESTION_DATA,
        )

        conn.commit()
        print("\n[OK] Migration completed successfully!")

        # Verify counts
        print("\nVerifying data counts:")
        tables = ["user", "project", "document", "run", "rundocument", "export", "suggestion"]
        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM "{table}"')
            count = cur.fetchone()[0]
            print(f"  {table}: {count}")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    migrate()
