# OpenMX 4.0 Singularity 容器构建记录

## 最终产物

| 容器 | 路径 | 大小 | 编译器 | BLAS |
|---|---|---|---|---|
| GNU 版 | `/mnt/shared/openmx4.0.sif` | 451 MB | GCC 11 + Gfortran | OpenBLAS |
| Intel 版 | `/mnt/shared/openmx4.0_intel.sif` | 4.2 GB | ICX 2025.0 + Gfortran | Intel MKL |
| GNU 定义文件 | `openmx4.0.def` | — | — | — |
| Intel 定义文件 | `openmx4.0_intel.def` | — | — | — |

> Note: Intel 版使用 Gfortran 编译 Fortran 代码 (ELPA 兼容性), ICX 编译 C 代码, MKL 提供数学库。
> 源码来自 `openmx4.0.tar.gz` (182 MB), 打了官方 `patch4.0.1.tar.gz` (30 KB) 补丁。

## 容器内容 (GNU 版)

- 基础系统: Ubuntu 22.04
- OpenMX 4.0 (源码位于 `/opt/openmx4.0/source/`)
- DFT_DATA19 (PAO + VPS 数据库, 内置在 `/opt/openmx4.0/DFT_DATA19/`)
- 编译器: GNU GCC/G++/Gfortran 11
- MPI: OpenMPI 4.1.2
- 数学库: FFTW3, ScaLAPACK (OpenMPI), OpenBLAS, LAPACK
- ELPA 2018.05.001 (特征值求解器, 源码自带)

## 容器内容 (Intel 版)

- 基础系统: Ubuntu 24.04 (intel/oneapi-hpckit)
- 编译器: Intel ICX 2025.0 (C), Gfortran 13 (Fortran)
- MPI: IntelMPI 2021.14
- 数学库: Intel MKL 2025.0 (含 ScaLAPACK, BLACS, FFTW 接口)
- ELPA 2018.05.001 (用 Gfortran 编译)

## 使用方式

### 基本用法

```bash
# 必须用相对路径传参! 见 ⚠️ 注意事项
cd /path/to/workdir

# GNU 版 (单进程, v4.0 强制 MPI 但可以用 -np 1)
singularity exec /mnt/shared/openmx4.0.sif mpirun -np 1 openmx input.dat

# Intel 版 (必须用容器内 mpirun)
singularity exec /mnt/shared/openmx4.0_intel.sif \
  mpirun -np 1 /opt/openmx4.0/work/openmx input.dat
```

### MPI 并行

```bash
# GNU 版
mpirun -np 4 singularity exec /mnt/shared/openmx4.0.sif openmx input.dat
singularity exec /mnt/shared/openmx4.0.sif mpirun -np 4 openmx input.dat

# Intel 版 (必须用容器内 mpirun, 与宿主 MPI 不兼容)
singularity exec /mnt/shared/openmx4.0_intel.sif \
  mpirun -np 4 /opt/openmx4.0/work/openmx input.dat
```

### Slurm 提交

模板文件: `slurm_scripts/run_gnu_4.0.sh`, `slurm_scripts/run_intel_4.0.sh`

```bash
# GNU
sbatch slurm_scripts/run_gnu_4.0.sh

# Intel
sbatch slurm_scripts/run_intel_4.0.sh
```

## ⚠️ 重要注意事项

### 必须使用相对路径传参

OpenMX 4.0 沿袭了 v3.9 的 bug:
`Make_InputFile_with_FinalCoord.c` 中拼接 `"./" + argv[1] + "#"` 创建临时文件。
当 `argv[1]` 是绝对路径 (如 `/mnt/shared/data/input.dat`) 时, 临时文件路径变为
`./mnt/shared/data/input.dat#`, 路径不存在导致 `fopen` 返回 NULL。

**已打补丁**: 在 `fopen` 后增加 NULL 检查, 输出错误信息并 `exit(1)`, 不再 segfault。

但仍然建议:
```bash
cd /path/to/data && singularity exec ... openmx input.dat     # ✅
singularity exec ... openmx /path/to/data/input.dat            # 补丁后报错退出
```

### MPI 是强制的

v4.0 没有串行模式。即使单核也必须用 `mpirun -np 1`。

### DFT_DATA19 自动发现

环境变量 `OPENMX_DFT_DATA_PATH=/opt/openmx4.0/DFT_DATA19` 自动设置。
代码中已打补丁: 优先读取环境变量, 然后是输入文件 `DATA.PATH`, 最后默认 `../DFT_DATA19`。

## 已应用的补丁

| 补丁 | 文件 | 说明 |
|---|---|---|
| Official 4.0.1 | `Band_DFT_Dosout.c`, `Mulliken_Charge.c`, `GaAs.dat` | 官方替换文件 |
| Patch A | `Input_std.c:100` | 添加 `getenv("OPENMX_DFT_DATA_PATH")` 支持 |
| Patch B | `Make_InputFile_with_FinalCoord.c:117,646` | `fopen` 后加 NULL 检查, 防止绝对路径 segfault |

### GNU makefile 修改

```makefile
CC = mpicc -O3 -ffast-math -fopenmp -fcommon -Dkcomp -DLEAK_DETECT \
     -I/usr/include -I/usr/lib/x86_64-linux-gnu/openmpi/include
FC = mpif90 -O3 -ffast-math -fopenmp -fallow-argument-mismatch -Dkcomp
LIB = -lfftw3 -lmpi -lmpi_mpifh -lscalapack-openmpi -llapack -lblas -lgfortran
```

### Intel makefile 修改

```makefile
MKLROOT = /opt/intel/oneapi/mkl/2025.0
CC = mpiicx -Wno-implicit-function-declaration -fcommon -O3 -march=native \
     -qopenmp -I${MKLROOT}/include/fftw -Dkcomp -DLEAK_DETECT
FC = mpif90 -O3 -march=native -fopenmp -Dkcomp \
     -fallow-argument-mismatch -ffree-line-length-none -fno-range-check
LIB = -lgfortran -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 \
      -lmkl_intel_lp64 -lmkl_intel_thread -lmkl_core \
      -lmkl_blacs_intelmpi_lp64 \
      -liomp5 -lpthread -lm -ldl -lifcore \
      -Wl,--allow-multiple-definition
```
## 容器状态

| 容器 | 路径 | 大小 | 状态 |
|---|---|---|---|
| Intel v4.0 | `/mnt/shared/openmx4.0_intel.sif` | 2.6 GB | ✅ Cluster/DC 求解器均正确, 补丁全 |

基于 `dc1394/openmx4.0-ubuntu22.04:0.2` (IFX 2026 + MKL 2026), 打上了:
- Official patch 4.0.1
- Patch A: `OPENMX_DFT_DATA_PATH` 环境变量回退 (含空字符串修复)
- Patch B: `Make_InputFile_with_FinalCoord.c` fopen NULL 检查

### 已知问题

**GNU 版**: Cluster/Band 求解器返回 NaN。已移除。

**Intel 版使用注意事项**:
- **必须在可写目录运行** (SIF 内文件系统只读, 写 `met.out` 会 segfault)
- **不需要** `DATA.PATH` 在输入文件 → env var 自动发现
- **必须用容器内的 `mpirun`** (宿主 MPI 与 Intel MPI 不兼容)
mkdir sandbox && tar xf /tmp/openmx40_gnu_fs.tar -C sandbox/
singularity build --fakeroot /mnt/shared/openmx4.0.sif sandbox/
singularity build --fakeroot /mnt/shared/openmx4.0.sif openmx4.0.def

# Intel: same pattern with intel/oneapi-hpckit
docker run -d --name openmx40_intel_build intel/oneapi-hpckit:latest sleep infinity
docker cp /tmp/openmx4.0_build_intel/openmx4.0/. openmx40_intel_build:/opt/openmx4.0/
docker exec openmx40_intel_build bash -c 'cd /opt/openmx4.0/source && make all'
docker commit openmx40_intel_build openmx40_intel
docker export openmx40_intel_build -o /tmp/openmx40_intel_fs.tar
mkdir sandbox_intel && tar xf /tmp/openmx40_intel_fs.tar -C sandbox_intel/
singularity build --force --fakeroot /mnt/shared/openmx4.0_intel.sif sandbox_intel/
singularity build --force --fakeroot /mnt/shared/openmx4.0_intel.sif openmx4.0_intel.def
```

## 性能对比 (待测量)

与 v3.9 相比, v4.0 的主要变化:
- MPI 变成强制要求
- Intel 版使用了不同的 Fortran 编译链 (Gfortran + MKL 而非纯 Intel)
- 增加了 leak detection 功能
