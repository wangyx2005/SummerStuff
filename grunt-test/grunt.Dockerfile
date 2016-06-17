FROM wangyx2005/change123
MAINTAINER "Yuxing Wang" <wangyx2005@gmail.com>

# Create a user and do everything as that user
VOLUME /data

# Install files
RUN mkdir -p /grunt.d
COPY grunt-docker /bin/grunt
COPY change123.gruntfile.yml /grunt.d/change.yml
COPY gruntfile.yml /gruntfile.yml

WORKDIR /data

CMD /bin/grunt /grunt.d/change.yml
EXPOSE 9901:9901
