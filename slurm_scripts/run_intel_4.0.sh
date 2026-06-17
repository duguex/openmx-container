#!/bin/bash
#SBATCH -p 6138
#SBATCH -N 1
#SBATCH -n 40
#SBATCH -J openmx4_intel
#SBATCH -t 0:10:00

ulimit -s unlimited
cd /path/to/data

SIF=/mnt/shared/openmx4.0_intel.sif

echo "=== Intel OpenMX 4.0 $(date) ==="
singularity exec $SIF mpirun -np $SLURM_NTASKS /opt/openmx4.0/work/openmx input.dat
echo "exit: $?"
