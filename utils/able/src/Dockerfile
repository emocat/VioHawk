FROM python:3.7

RUN pip3 install torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu113
RUN pip3 install websockets pandas sklearn tqdm wsaccel shapely 

RUN pip3 install rtamt
RUN pip3 install antlr4-python3-runtime==4.8

COPY bridge/PythonAPImaster /tmp/PythonAPIMaster

WORKDIR /tmp/PythonAPIMaster
RUN pip3 install --user -e .
RUN pip3 install -r requirements.txt --user .
RUN pip3 install --user protobuf==3.19.0

WORKDIR /usr/src/app

ENV PYTHONPATH "${PYTHONPATH}:/usr/src/app"

CMD nvidia-smi