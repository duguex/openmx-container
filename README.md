# OpenMX Container

Singularity container builds, Slurm job scripts, and source code for OpenMX 3.9 / 4.0.

## Directory Structure

| Path | Description |
|------|-------------|
| `openmx4.0/` | OpenMX 4.0 source code |
| `slurm_scripts/` | Job submission scripts (GNU / Intel) |
| `build/` | Container build records |
| `openmx4.0.def` | GNU Singularity definition |
| `openmx4.0_intel.def` | Intel Singularity definition |
| `build_notes.md` | Container build instructions |
| `v4_container_notes.md` | v4.0 specific notes |
| `benchmark_results.md` | Performance benchmark data |
| `RESOURCES.md` | Download resource list |

## Containers

| Container | Compiler | Size |
|-----------|----------|------|
| openmx3.9.sif (GNU) | GCC 11 + OpenBLAS | 417 MB |
| openmx3.9_intel.sif (Intel) | ICX 2025 + MKL | 4.1 GB |
| openmx4.0_intel.sif (Intel) | IFX 2026 + MKL | 2.6 GB |

## Input File Generation

For `omx-gen` and `omx-db` CLI tools, see the companion project:

→ `~/omx/` (omx-tools Python package)

## Quick Use

```bash
# Intel v4.0
singularity exec /mnt/shared/openmx4.0_intel.sif \
  /openmx4.0/work/openmx input.dat

# Slurm submission
sbatch slurm_scripts/run_intel_4.0.sh
```
