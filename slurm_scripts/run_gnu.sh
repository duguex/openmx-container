#!/bin/bash
#SBATCH -p 6138
#SBATCH -N 1
#SBATCH -n 40
#SBATCH -J openmx_gnu
#SBATCH -t 0:10:00

ulimit -s unlimited
cd /path/to/data

SIF=/mnt/shared/openmx3.9.sif

echo "=== GNU OpenMX $(date) ==="
singularity exec $SIF mpirun -np $SLURM_NTASKS /opt/openmx3.9/work/openmx input.dat
echo "exit: $?"
