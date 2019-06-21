# FROM python:3.7
FROM ubuntu:latest

ADD . /

RUN apt-get update 
RUN apt-get install -y gnupg2
RUN echo "deb http://downloads.skewed.de/apt/bionic bionic universe" >> /etc/apt/sources.list
RUN echo "deb-src http://downloads.skewed.de/apt/bionic bionic universe" >> /etc/apt/sources.list
RUN apt-key adv --keyserver pgp.skewed.de --recv-key 612DEFB798507F25
RUN apt-get update
RUN apt-get install -y python3-graph-tool

RUN apt-get install -y python-pip
RUN pip install -r requirements.txt