# OpenMX Container Benchmark Results

## Performance Breakdown

### Small: 8 Si atoms, 4×4×4 k-grid (64 k-points), 29 SCF
Hardware: 6138 cluster, Xeon Gold 6138 @ 2.00GHz, 40 cores/node

#### GNU (OpenMPI) — host or container mpirun

| MPI | DFT total | Diagonalization | Wall time | Speedup |
|---|---|---|---|---|
| 8 | 16.44 s | 3.97 s | ~17 s | 1.00x |
| 16 | 16.76 s | 3.10 s | ~18 s | 0.98x |
| 24 | 18.15 s | 3.42 s | ~19 s | 0.91x |
| 32 | 19.03 s | 2.93 s | ~20 s | 0.86x |
| 40 | 18.69 s | 2.83 s | ~19 s | 0.88x |

No speedup beyond 8 cores — the problem is too small.

#### Intel (IntelMPI) — container mpirun only

| MPI | DFT total | Diagonalization | Wall time | Speedup |
|---|---|---|---|---|
| 8 | 16.43 s | 4.18 s | ~17 s | 1.00x |
| 16 | 16.06 s | 3.25 s | ~17 s | 1.02x |
| 24 | 17.98 s | 3.49 s | ~19 s | 0.91x |
| 32 | 16.16 s | 2.18 s | ~17 s | 1.02x |
| 40 | 17.42 s | 2.50 s | ~18 s | 0.94x |

Same conclusion: no speedup above 8 cores.

### Single-core comparison (local 7940x @ 3.10GHz)

| Version | Time | vs GNU |
|---|---|---|
| GNU (GCC 11 + OpenBLAS) | 93.4 s | 1.00x |
| Intel (ICX 2025 + MKL) | 76.5 s | **1.22x** |

Intel MKL provides ~22% speedup on single-core diagonalization-heavy workloads.

### Correct vs incorrect path behavior

| Invocation | GNU (OpenMPI) | Intel (IntelMPI) |
|---|---|---|
| `openmx Si8.dat` (relative) | ✅ Normal exit | ✅ Normal exit |
| `openmx /abs/path/Si8.dat` (absolute) | ❌ Segfault | ❌ Segfault → OOM |

Both failures caused by `Make_InputFile_with_FinalCoord.c` path concatenation bug.

## System Information

### 6138 node (R5500-G4)
- CPU: 2× Xeon Gold 6138 @ 2.00GHz, 20 cores/socket, no HT
- Memory: 187 GB
- OS: Ubuntu 24.04, kernel 6.8.0-117-generic
- MPI: OpenMPI 4.1.2 (host), IntelMPI 2021.14 (container)
- Filesystem: NFSv4.2

### Local workstation (7940x)
- CPU: Intel i9-7940X @ 3.10GHz, 14 cores, 28 threads
- Memory: 64 GB
- OS: Ubuntu 22.04
