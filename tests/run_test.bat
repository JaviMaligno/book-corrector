@echo off
set RUN_GEMINI_INTEGRATION=1
set GOOGLE_API_KEY=AIzaSyCJwDcNRrE0f1gwhnDUsM-bb6jMZT3XW7A
.venv\Scripts\python.exe -m pytest tests\test_gemini_live.py::test_gemini_live_corrections_and_proper_names -v -s
