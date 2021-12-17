FROM python:3.8
WORKDIR /app/src
COPY src ./
COPY requirements.txt ./
RUN pip install -r requirements.txt
CMD [ "python", "./worker.py" ]
