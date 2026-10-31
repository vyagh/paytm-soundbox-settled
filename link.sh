#!/usr/bin/env bash
host=vivek@100.124.148.103

while true; do
  echo "$(date +%T) link: connecting"
  ssh -N -R 8080:127.0.0.1:8080 \
    -i ~/.ssh/id_ed25519 \
    -o BatchMode=yes \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=10 \
    -o ServerAliveCountMax=3 \
    "$host" &
  pid=$!
  sleep 2
  kill -0 "$pid" 2>/dev/null && echo "$(date +%T) link: up"
  trap 'kill "$pid" 2>/dev/null; exit 0' INT TERM
  wait "$pid"
  echo "$(date +%T) link: dropped, retrying in 3s"
  sleep 3
done
