# OpenMX 3.9 Singularity Container

Standalone OpenMX 3.9 Singularity containers for HPC clusters.

## Files

| File | Description |
|---|---|
| `build_notes.md` | Full build documentation, issues, and resolutions |
| `openmx3.9.def` | Singularity definition file (GNU build) |
| `intel_build.sh` | Build script for Intel oneAPI version |
| `slurm_scripts/run_gnu.sh` | Slurm submission template (GNU) |
| `slurm_scripts/run_intel.sh` | Slurm submission template (Intel) |
| `examples/Si8.dat` | Test input: 8-atom Si diamond |
| `benchmark_results.md` | Performance scaling results |

## Containers

| Container | Path | Size |
|---|---|---|
| GNU (default) | `/mnt/shared/openmx3.9.sif` | 417 MB |
| Intel | `/mnt/shared/openmx3.9_intel.sif` | 4.1 GB |
