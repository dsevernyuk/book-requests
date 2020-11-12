FROM python:alpine3.8 
RUN mkdir /app
WORKDIR /app
COPY ./requirements.txt /app/
RUN pip install -r requirements.txt
COPY ./app/* /app/
EXPOSE 5000
ENTRYPOINT [ "python" ] 
CMD [ "main.py" ]
