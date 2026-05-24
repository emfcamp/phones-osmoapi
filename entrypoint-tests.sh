#!/bin/sh

nohup osmo-hlr -c /etc/osmocom/osmo-hlr.cfg &
nohup osmo-msc -c /etc/osmocom/osmo-msc.cfg &
nohup osmo-mgw -c /etc/osmocom/osmo-mgw.cfg &
nohup osmo-stp -c /etc/osmocom/osmo-stp.cfg &
nohup osmo-bsc -c /etc/osmocom/osmo-bsc.cfg &

cd /app
uv run pytest