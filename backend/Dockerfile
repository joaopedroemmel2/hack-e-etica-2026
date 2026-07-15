FROM python:3.12-slim AS production
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN addgroup --system --gid 1001 flowlog && adduser --system --uid 1001 --ingroup flowlog flowlog
COPY pyproject.toml requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade "pip>=26.1.2" && pip install --no-cache-dir .
COPY --chown=flowlog:flowlog app ./app
COPY --chown=flowlog:flowlog alembic ./alembic
COPY --chown=flowlog:flowlog alembic.ini ./
COPY --chown=flowlog:flowlog scripts ./scripts
RUN chmod +x scripts/start.sh
USER flowlog
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:3000/api/health')"
CMD ["./scripts/start.sh"]
