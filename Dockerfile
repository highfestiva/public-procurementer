FROM python:3.11

RUN apt update

RUN pip install --upgrade pip
RUN pip install flask groq pypdf

ADD . /usr/local/public-procurementer/

WORKDIR /usr/local/public-procurementer
CMD ["./app.py"]
#CMD ["sleep", "10000"]
