#!/usr/bin/env bash

##--------------------------------------------------------------------
## Copyright (c) 2020 Dianomic Systems
##
## Licensed under the Apache License, Version 2.0 (the "License");
## you may not use this file except in compliance with the License.
## You may obtain a copy of the License at
##
##     http://www.apache.org/licenses/LICENSE-2.0
##
## Unless required by applicable law or agreed to in writing, software
## distributed under the License is distributed on an "AS IS" BASIS,
## WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
## See the License for the specific language governing permissions and
## limitations under the License.
##--------------------------------------------------------------------

##
## Author: Mark Riddoch, Akli Rahmoun
## Modified by: Markus Oja
## from https://github.com/fledge-power/fledgepower-deployment/blob/main/s61850-n104-ubuntu2004/fledge/fledge-install-dispatcher.sh
##  Changes: 
##      Fledge 2.3.0 -> 2.4.0
FLEDGEDISPATCHVERSION=2.4.0
RELEASE=2.4.0
OPERATINGSYSTEM=ubuntu2004
ARCHITECTURE=x86_64
FLEDGELINK="http://archives.fledge-iot.org/$RELEASE/$OPERATINGSYSTEM/$ARCHITECTURE"

wget --no-check-certificate ${FLEDGELINK}/fledge-service-dispatcher_${FLEDGEDISPATCHVERSION}_${ARCHITECTURE}.deb
dpkg --unpack ./fledge-service-dispatcher_${FLEDGEDISPATCHVERSION}_${ARCHITECTURE}.deb
apt-get install -yf
apt-get clean -y
