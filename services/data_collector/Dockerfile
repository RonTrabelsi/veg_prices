# pull official base image
FROM python:3.11.3

# install netcat
RUN apt-get update && \
    apt-get install -y netcat && \
    apt-get clean

# set environment varibles
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# set working directory
WORKDIR /usr/src/data_collector

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/data_collector/requirements.txt
RUN pip install -r requirements.txt

# add app
COPY . /usr/src/data_collector

# enable entrypoint
RUN chmod +x /usr/src/data_collector/entrypoint.sh
