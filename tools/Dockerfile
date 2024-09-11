FROM registry.gitlab.com/gemseo/dev/gemseo/multi-python

ARG SCILAB_VERSION=5.5.2

# Install scilab.
# Scilab requires java, libnsl and a x11 server for headless display.
RUN  dnf -y install java-1.8.0-openjdk \
                    libnsl \
                    xorg-x11-server-Xvfb \
  && dnf clean all \
  && curl -SL https://www.scilab.org/download/$SCILAB_VERSION/scilab-$SCILAB_VERSION.bin.linux-x86_64.tar.gz \
  |  tar -xzC /opt

ENV PATH=/opt/scilab-$SCILAB_VERSION/bin:$PATH
