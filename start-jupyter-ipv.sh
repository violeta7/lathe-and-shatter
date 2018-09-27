#
set -x

if [ -z $(docker images -q tetgen:0.1) ]
then
  if [ -f docker/docker-tetgen_0_1.tar.gz ]
  then
    gzip -d -c docker/docker-tetgen_0_1.tar.gz | docker load
  else
    docker build -t tetgen:0.1 docker
    docker save tetgen:0.1 | gzip -9 -c - > docker/docker-tetgen_0_1.tar.gz
  fi
fi

docker run --name tetgen -d \
    -p 8888:8888 \
    -v $(pwd):$(pwd) \
    -w $(pwd)/ \
    tetgen:0.1 \
    bash -c 'set -x
source activate tetgen
password=ubuntu
hash=$(python -c "from notebook.auth import passwd; print(passwd("\""$password"\""))")
exec jupyter notebook --allow-root --ip 0.0.0.0 --port 8888 --no-browser --NotebookApp.password="$hash"
'
