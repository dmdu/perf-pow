#!/bin/bash

dir=/var/log/power
out=$dir/output
log=$dir/log
sleep_period=5
repeats=1

np_lim=8

rm -rf $out*
rm -rf $log

cat $0 > $dir/script

np=1
until [ $np -gt $np_lim ]
do

#cmd="mpiexec -n $np --allow-run-as-root /opt/hpgmg/arm64/bin/hpgmg-fe sample -local 1e4 -op_type poisson2 -repeat 10 -log_summary"
cmd="mpiexec -n $np --allow-run-as-root /opt/hpgmg/arm64/bin/hpgmg-fe sample -local 1e3 -op_type poisson2 -log_summary"

c=0
until [ $c -ge $repeats ]
do
  echo "Experiment: $c/$repeats"

  echo -n "$np,$c" | tee -a $log
  echo -n ",`date -u +%s`,`date -u`" | tee -a $log
  $cmd 2>&1 | tee -a "$out-$np-$c"

  sum=`cat "$out-$np-$c" | grep GF | awk '{print $12}' | paste -sd+ | bc`
  count=`cat "$out-$np-$c" | grep GF | wc -l`
  avg=`echo "scale=7;$sum/$count" | bc`

  echo ",`date -u +%s`,`date -u`,$avg" | tee -a $log

  echo "Sleeping: $sleep_period"
  sleep $sleep_period

  c=$[$c+1]
done

np=$[$np+1]
done
