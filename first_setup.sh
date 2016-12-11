virtualenv env
source env/bin/activate
pip install -U pip
pip install -Ur requirements.txt
python -m grpc.tools.protoc -I. --python_out=. --grpc_python_out=. *.proto
deactivate
