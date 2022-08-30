#!/bin/bash

diagrams=( 
    overview 
    1_analyze
    2_plaatsen_VPLs
    3_verplaatsen_VPLs
    4_plaatsen_nonVPLs
    5_uitbreiden_nonVPLs
    6_plaatsen_Blijst
    7_uitbreiden_Blijst
    8_validatie
    9_afwijzing
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
    docker run -u 1000  -it -v /home/harm/Documents/amsterdam/repositories/makkelijkemarkt/makkelijkemarkt-allocation/diagrams:/data minlag/mermaid-cli -i /data/src/$i.mmd -o /data/img/$i.$f
done

done
