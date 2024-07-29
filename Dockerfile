FROM python:3.12-slim

COPY . /app

RUN pip3 install flask 

RUN pip3 install flask-restx

RUN pip3 install flask-cors

WORKDIR /app

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]