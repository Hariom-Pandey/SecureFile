"""Flask entrypoint for `flask --app wsgi:app run` from repository root."""
from project.main import create_app

app = create_app()
