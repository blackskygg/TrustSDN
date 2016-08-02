#!/bin/bash
for i in $(seq 1000);
do curl -k --key user_9E679BF3EDBF0684.key --cert user_9E679BF3EDBF0684.crt https://localhost:8080/v1.0/topology/switches >>/dev/null;
echo $i;
done;
   
