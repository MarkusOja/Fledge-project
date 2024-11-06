FROM ubuntu:20.04

LABEL author="Akli Rahmoun"
LABEL modified="Markus Oja"

# from https://github.com/fledge-power/fledgepower-deployment/blob/main/s61850-n104-ubuntu2004/fledge/fledge.dockerfile
# changes:
#   fledge to version 2.4.0
#   removed ALL plugin installs

# Set FLEDGE version, distribution, and platform
ARG FLEDGEVERSION=2.4.0
ARG RELEASE=2.4.0
ARG OPERATINGSYSTEM=ubuntu2004
ARG ARCHITECTURE=x86_64
ARG FLEDGELINK="http://archives.fledge-iot.org/${RELEASE}/${OPERATINGSYSTEM}/${ARCHITECTURE}"


ENV FLEDGE_ROOT=/usr/local/fledge

# Avoid interactive questions when installing Kerberos
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get dist-upgrade -y && apt-get install --no-install-recommends --yes \
    git \
    iputils-ping \
    inetutils-telnet \
    nano \
    rsyslog \
    sed \
    wget \
    snmp \
    cmake g++ make build-essential autoconf automake uuid-dev \
    libgtest-dev libgmock-dev && \
    echo '=============================================='
    
RUN mkdir ./fledge && \
    wget -O ./fledge/fledge-${FLEDGEVERSION}-${ARCHITECTURE}.deb --no-check-certificate ${FLEDGELINK}/fledge_${FLEDGEVERSION}_${ARCHITECTURE}.deb && \   
    dpkg --unpack ./fledge/fledge-${FLEDGEVERSION}-${ARCHITECTURE}.deb && \
    sed '/^.*_fledge_service$/d' /var/lib/dpkg/info/fledge.postinst > /fledge.postinst && \
    mv /var/lib/dpkg/info/fledge.postinst /var/lib/dpkg/info/fledge.postinst.save && \
    apt-get install -yf && \
    mkdir -p /usr/local/fledge/data/extras/fogbench && \
    chmod +x /fledge.postinst && \
    /fledge.postinst && \
    rm -f /*.tgz && \ 
    rm -rf -r /fledge && \
    apt-get autoremove -y && \
    apt-get clean -y && \
    rm -rf /var/lib/apt-get/lists/ && \
    echo '=============================================='

COPY fledge-install-include.sh /tmp/

RUN chmod +x /tmp/fledge-install-include.sh && \
    /tmp/fledge-install-include.sh && \
    echo '=============================================='

COPY fledge-install-dispatcher.sh /tmp/

RUN chmod +x /tmp/fledge-install-dispatcher.sh && \
    /tmp/fledge-install-dispatcher.sh && \
    echo '=============================================='

###### INSTALL PLUGINS FROM FOLDER #####
# Copy the plugins to the container
COPY filter/add-uuid /usr/local/fledge/python/fledge/plugins/filter/add-uuid
COPY filter/transform-to-asyncapi /usr/local/fledge/python/fledge/plugins/filter/transform-to-asyncapi
# next one needs kafka-python which is not installed per default
COPY north/send-to-kafka /usr/local/fledge/python/fledge/plugins/north/send-to-kafka
RUN pip3 install kafka-python
COPY south/get-from-rest /usr/local/fledge/python/fledge/plugins/south/get-from-rest


WORKDIR /usr/local/fledge
COPY start.sh start.sh


RUN echo "sleep 30" >> start.sh && \
    echo "tail -f /var/log/syslog" >> start.sh && \
    chmod +x start.sh

VOLUME /usr/local/fledge 

# Fledge API port for FELDGE API http and https and Code Server
EXPOSE 8081 1995 8080 2404 2405

# start rsyslog, FLEDGE, and tail syslog
CMD ["/bin/bash","/usr/local/fledge/start.sh"]
