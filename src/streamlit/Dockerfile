# V1
FROM python:3.12-slim

LABEL version="0.1"

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN groupadd -g 1001 app && \
    useradd -u 1001 -g app -m app

# Install pip requirements
COPY requirements.txt /home/app
COPY app.py /home/app
COPY lib.py /home/app

WORKDIR /home/app
RUN python -m pip install -r requirements.txt

RUN chown -R app:app /home/app

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

USER app
WORKDIR /home/app
ENTRYPOINT ["streamlit", "run", "/home/app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
