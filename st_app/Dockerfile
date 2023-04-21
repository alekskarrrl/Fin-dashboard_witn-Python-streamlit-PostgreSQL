FROM python:3.9
WORKDIR /app
COPY ./ ./
RUN python -m pip install --upgrade pip && pip install -r requirements.txt
EXPOSE 8501

ENTRYPOINT ["streamlit", "run", "dashboard.py"]