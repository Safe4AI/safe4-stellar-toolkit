FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY apps ./apps
COPY packages ./packages
COPY scripts ./scripts
COPY tests ./tests
COPY docs ./docs
COPY README.md ./
COPY HACKATHON_SUBMISSION.md ./
COPY DEMO_SCRIPT.md ./
COPY PITCH.md ./
COPY STELLAR_ADAPTATION.md ./
COPY LICENSE ./
COPY .env.example ./

EXPOSE 8080

CMD ["sh", "-c", "python -m uvicorn apps.api.main:app --host 0.0.0.0 --port ${PORT:-8080} --proxy-headers --forwarded-allow-ips='*'"]
