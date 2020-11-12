FROM nvidia/cuda:10.2-cudnn7-devel-ubuntu18.04

# Install Python 3.8
RUN apt update && \
    apt install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa && \
    apt update && \
    apt install -y python3.8 python3-pip && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1 && \
    update-alternatives --install /usr/bin/python python /usr/bin/python3.8 1 && \
    update-alternatives --install /usr/bin/pip pip /usr/bin/pip3 1

# OpenGL is needed for OpenCV
RUN apt install -y libgl1-mesa-glx

# Install poetry
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false

# Install dependencies
COPY ./pyproject.toml ./poetry.lock* /app/
RUN poetry install --no-root --no-dev

# Install dependencies
RUN mkdir -p /chess
WORKDIR /chess
COPY poetry.lock pyproject.toml ./
RUN poetry install
ENV PYTHONPATH "/chess:${PYTHONPATH}"

# Fix for tensorboard
RUN poetry run pip install wheel

# Setup data mount
RUN mkdir -p /data
ENV DATA_DIR /data
VOLUME /data

# Setup config mount
RUN mkdir -p /config
ENV CONFIG_DIR /config
VOLUME /config

# Setup run mount
RUN mkdir -p /chess/runs
ENV RUN_DIR /chess/runs
VOLUME /chess/runs

# Setup results mount
RUN mkdir -p /chess/results
ENV RESULTS_DIR /chess/results
VOLUME /chess/results

# Setup models mount
RUN mkdir -p /chess/models
ENV MODELS_DIR /chess/models
VOLUME /chess/models

# Copy files
COPY chesscog ./chesscog

# Scratch volume
VOLUME [ "/chess/scratch" ]

# Entrypoint
CMD poetry run tensorboard --logdir ./runs --host 0.0.0.0 --port 9999  & \
    poetry run jupyter lab --no-browser --allow-root --ip 0.0.0.0 --port 8888 --NotebookApp.password "sha1:ee6cc5205a00:1c3b701b60c0abba31f350d40912b3769acccc85"