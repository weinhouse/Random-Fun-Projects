#!/bin/bash

# assumes that files from our android cameras create mp4 files.
# run with year as argument year should have two directories yyyy_SummerFall and yyyy_Winter_Spring
# usage rip_a_years_movies.sh 2019

# If you need to rotate movies:
# ffmpeg -noautorotate -r 30 -i '2015_Summer_Fall/2015-06-12 16.35.57.mp4' -vf "transpose=clock" -r 30 -acodec copy 2015_renamed/$(date +%s).mp4
# Concatinate: https://trac.ffmpeg.org/wiki/Concatenate

year=$1

mkdir ${year}_renamed_movies

find ${year}_* -iregex .*mp4.* -exec cp  {} ${year}_renamed_movies/ \;

pushd ${year}_renamed_movies

number=1

ls *.mp4 | while read line; do mv "${line}" "${number}.mp4"; export number=$(expr $number + 1);done

ls *.mp4 | while read line; do echo "file ${line}";done | tee movies.txt

ffmpeg -f concat -i movies.txt -c copy ${year}_family_movies.mp4
