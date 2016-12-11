virtualenv env
source env/bin/activate
pip install -U pip
pip install -Ur misc/requirements.txt
./scripts/make_proto.sh
deactivate
