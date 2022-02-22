#!/bin/bash

diagrams=( 
    overview 
    fase_1 
    fase_2-3 
    fase_4
    fase_5-6-7-8
    fase_9-10-11-12-13
    fase_14-15-16-17
    fase_18-19-20-21
    fase_22
    fase_23
    vinden_kramen
    vinden_uitbreiding
)

filetypes=(
    svg
    png
)

for f in "${filetypes[@]}"
do

for i in "${diagrams[@]}"
do
    docker run -u 1000  -it -v /home/johan/Projects/amsterdam/origin/makkelijkemarkt-allocations/diagrams:/data minlag/mermaid-cli -i /data/src/$i.mmd -o /data/img/$i.$f
done

done
