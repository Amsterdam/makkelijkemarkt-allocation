#!/bin/bash

diagrams=( 
    overview 
    # fase_1 
    # fase_2-3-4 
    # fase_5
    # fase_6-7-8-9-10-11
    # fase_12-13-14-15-16
    # fase_17-18-19-20
    # fase_21-22-23-24
    # fase_25
    # fase_26
    # vinden_kramen
    # vinden_uitbreiding
)

filetypes=(
    svg
    png
)

for f in "${filetypes[@]}"
do

for i in "${diagrams[@]}"
do
    docker run -u 1000  -it -v /home/harm/Documents/amsterdam/repositories/makkelijkemarkt/makkelijkemarkt-allocation/diagrams:/data minlag/mermaid-cli -i /data/src/$i.mmd -o /data/img/$i.$f
done

done
