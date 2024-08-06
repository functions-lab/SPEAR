#!/bin/bash

time=$1

deviceTx=$2
rateTx=$3
clockTx=$4
fileTx=$5
carrierTx=$6
gainTx=$7

deviceRx=$8
rateRx=$9
clockRx=${10}
fileRx=${11}
carrierRx=${12}
gainRx=${13}

# python3 "$(dirname -- "${BASH_SOURCE[0]}")"/USRP_mult.py \
#     --addr $deviceTx --rate $rateTx --time 100 --sync 0 --clock $clockTx \
#     --fileTx $fileTx --freqTx $carrierTx --gainTx $gainTx &
# pid=$!
# sleep 4s
python3 "$(dirname -- "${BASH_SOURCE[0]}")"/USRP_mult.py \
    --addr $deviceRx --rate $rateRx --time $time --sync 0 --clock $clockRx \
    --fileRx $fileRx --freqRx $carrierRx --gainRx $gainRx
kill -9 $pid
