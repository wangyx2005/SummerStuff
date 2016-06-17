FROM pesscara/grunt
MAINTAINER "Yuxing Wang" <wangyx2005@gmail.com>
USER root

WORKDIR /
COPY change.sh change.sh
COPY gruntfile.yml /grunt.d/change.yml

CMD /bin/grunt /grunt.d/change.yml
EXPOSE 9901:9901
