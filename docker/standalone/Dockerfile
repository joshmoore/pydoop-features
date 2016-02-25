FROM centos:centos6
MAINTAINER simone.leo@crs4.it

ADD install_maven.sh /
ADD set_bf_ver.py /
ADD install_pydoop_features.sh /

RUN yum -y update
RUN yum -y install centos-release-SCL epel-release
RUN yum -y install \
    tar \
    git \
    python27 \
    python27-scipy \
    python27-devel \
    java-1.8.0-openjdk-devel \
    fftw-static \
    fftw-devel \
    libtiff-devel \
    gcc-c++ \
    swig
RUN echo ". /opt/rh/python27/enable" >/etc/profile.d/python.sh
RUN bash install_maven.sh
RUN bash install_pydoop_features.sh