FROM python:3.9-slim
WORKDIR /home/projects/okmakbot
RUN apt-get update
#RUN apt-get upgrade
RUN apt-get install -y python3-pip
RUN pip3 install aiogram
RUN apt-get clean && \
    apt-get -y autoclean && \
    apt-get -y autoremove
CMD ['python3', 'okmakbot.py']