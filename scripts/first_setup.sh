virtualenv env
source env/bin/activate
pip install -U pip
pip install -Ur misc/requirements.txt
python -m grpc.tools.protoc -I. --python_out=proto/ --grpc_python_out=proto/ proto/*.proto
deactivate
