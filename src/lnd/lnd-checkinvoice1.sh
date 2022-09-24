#!/bin/sh

## latest working version, to be replaced by more verbose lnd-invoicetoqr.sh

var_rHash=$(cat /home/pi/ChicksOnTheBlocks/src/lnd/temp/tempInvoice.txt | grep r_hash | cut -d '"' -f 4)

var_macaroonPath=/home/pi/ChicksOnTheBlocks/src/lnd/invoice.macaroon
var_tlsCertPath=/home/pi/ChicksOnTheBlocks/src/lnd/tls.cert
var_rpcServer=178.26.165.115:10009

var_paymentState=$(/home/pi/ChicksOnTheBlocks/src/lnd/lncli-arm/lncli --macaroonpath $var_macaroonPath --tlscertpath $var_tlsCertPath --rpcserver $var_rpcServer lookupinvoice $var_rHash | grep state | cut -d '"' -f 4)

case $var_paymentState in
  "SETTLED") echo "SETTLED";;
  "OPEN") echo "OPEN";;
  *) echo "Error"
esac
