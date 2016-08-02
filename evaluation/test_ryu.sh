#!/bin/bash

for i in $(seq 500);
do curl http://localhost:8080/v1.0/topology/switches >> out;
done;
   
