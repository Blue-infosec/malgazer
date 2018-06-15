FROM python:3

#RUN cd /; git clone https://github.com/keithjjones/malgazer.git
COPY requirements.txt /
RUN pip install -r /requirements.txt
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /malgazer
CMD ["python", "/malgazer/tornado/malgazer.py"]