FROM python:3.10-slim-bookworm

WORKDIR /app

# 1. Création d'un utilisateur et d'un groupe non-root sécurisés
RUN addgroup --system appgroup && adduser --system --group appuser

# 2. Mise à jour de l'OS et des outils
RUN apt-get update && apt-get upgrade -y && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Installation des dépendances
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copie du code source
COPY . .

# 5. Changement de propriétaire : on donne le dossier /app à notre utilisateur restreint
RUN chown -R appuser:appgroup /app

# 6. Bascule sur l'utilisateur non-root pour l'exécution
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]