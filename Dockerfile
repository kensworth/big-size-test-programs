FROM python:2.7.12

# Some stuff that everyone has been copy-pasting
# since the dawn of time.
ENV PYTHONUNBUFFERED 1

# Bundle app source
RUN mkdir -p /src
WORKDIR /src
COPY . /src

# Install our requirements.
RUN pip install -U pip
RUN pip install -Ur requirements.txt
RUN python -m grpc.tools.protoc -I. --python_out=. --grpc_python_out=. *.proto

EXPOSE  8000
CMD ["python", "test-server.py"]
