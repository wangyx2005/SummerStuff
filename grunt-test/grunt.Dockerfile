FROM ubuntu
MAINTAINER "Yuxing Wang" <wangyx2005@gmail.com>

# Create a user and do everything as that user
VOLUME /data

# Install files
RUN mkdir -p /grunt.d
COPY grunt-docker /bin/grunt
COPY gruntfile.yml /gruntfile.yml
COPY change.sh /change.sh
COPY change.gruntfile.yml /grunt.d/change.yml

WORKDIR /data

CMD /bin/grunt /grunt.d/change.yml
EXPOSE 9901:9901
