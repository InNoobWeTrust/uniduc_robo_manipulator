#!/usr/bin/env sh

build_image() {
    docker build --tag ros:automata .
}

create_container() {
    docker container create -it \
        --network host \
        --env ROS_HOSTNAME="$(hostname)" \
        --env ROS_MASTER_URI=http://$(hostname):11311 \
        --env DISPLAY="$DISPLAY" \
        -v "$(pwd)/test":/catkin_ws \
        -v ~/.ssh:/root/.ssh \
        -v "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
        --name automata \
        ros:automata
}

start_container() {
    docker start automata
}

attach_container() {
    docker exec -it automata bash
}

stop_container() {
    docker stop automata
}

prune() {
    docker container prune -f && docker image prune -f
}

for i in $@
do
    case $i in
        build)
            build_image
            shift
            ;;
        create)
            create_container
            shift
            ;;
        start)
            start_container
            shift
            ;;
        attach)
            attach_container
            shift
            ;;
        stop)
            stop_container
            shift
            ;;
        prune)
            prune
            shift
            ;;
    esac
done

