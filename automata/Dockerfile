FROM ros:melodic

EXPOSE 11311

RUN apt-get update && \
    apt-get install -y python3-pip python3-yaml && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV DISPLAY=localhost:1

COPY requirements.txt requirements.txt

# Fix python3 problem with ROS
RUN pip3 install rospkg catkin_pkg

RUN pip3 install -r requirements.txt && \
    rm requirements.txt

WORKDIR /catkin_ws
