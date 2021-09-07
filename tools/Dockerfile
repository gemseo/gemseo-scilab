ARG FEDORA_VERSION=34

FROM fedora:$FEDORA_VERSION

ARG TOX_VERSION=3.24.1

# Fedora tox is outdated, install with pip.
# Scilab requires java, libnsl and a x11 server for headless display.
RUN  dnf -y update \
  && dnf -y install python \
  && dnf -y install pip \
  && dnf -y install python27 \
  && dnf -y install python36 \
  && dnf -y install python37 \
  && dnf -y install python38 \
  && dnf -y install python39 \
  && dnf -y install git \
  && dnf -y install libnsl \
  && dnf -y install java-1.8.0-openjdk \
  && dnf -y install xorg-x11-server-Xvfb \
  && dnf clean all \
  && python -m pip install tox==$TOX_VERSION

ARG SCILAB_VERSION=5.5.2

# Install scilab
RUN curl -SL https://www.scilab.org/download/$SCILAB_VERSION/scilab-$SCILAB_VERSION.bin.linux-x86_64.tar.gz \
  | tar -xzC /opt
ENV PATH=/opt/scilab-$SCILAB_VERSION/bin:$PATH
