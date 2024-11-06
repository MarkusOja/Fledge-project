FROM nginx:latest

LABEL author="Akli Rahmoun"
LABEL modified="Markus Oja"

# from https://github.com/fledge-power/fledgepower-deployment/blob/main/s61850-n104-ubuntu2004/fledge-gui/fledge-gui.dockerfile
# changes:
#   fledge upgraded to version 2.4.0

ARG FLEDGEVERSION=2.4.0
ARG RELEASE=2.4.0

ARG OPERATINGSYSTEM=ubuntu2004
ARG ARCHITECTURE=x86_64
ARG FLEDGELINK="http://archives.fledge-iot.org/${RELEASE}/${OPERATINGSYSTEM}/${ARCHITECTURE}"

RUN apt-get update

RUN apt-get install -y wget && \ 
    wget --no-check-certificate ${FLEDGELINK}/fledge-gui_${FLEDGEVERSION}.deb && \
    dpkg --unpack fledge-gui_${FLEDGEVERSION}.deb && \
    rm -r /usr/share/nginx/html && \
    mv /var/www/html /usr/share/nginx && \
    mv /usr/share/nginx/html/fledge.html /usr/share/nginx/html/index.html && \
    chown -R  nginx.nginx /usr/share/nginx/html && \
    apt-get clean -y && \
    rm -rf /var/lib/apt/lists/ && \
    rm -rf /var/www/

# Fledge GUI ports
EXPOSE 8080