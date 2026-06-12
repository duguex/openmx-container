# OpenMX 3.9 独立 Singularity 容器构建记录

## 最终产物

| 容器 | 路径 | 大小 | 编译器 | BLAS |
|---|---|---|---|---|
| GNU 版 | `/mnt/shared/openmx3.9.sif` | 417 MB | GCC 11 + Gfortran | OpenBLAS |
| Intel 版 | `/mnt/shared/openmx3.9_intel.sif` | 4.1 GB | ICX 2025.0 + IFX | Intel MKL |
| 定义文件 | `openmx3.9.def` | — | — | — |

## 容器内容 (GNU 版)

- 基础系统: Ubuntu 22.04
- OpenMX 3.9 (源码来自 `/home/duguex/developing/openmx3.9/`)
- DFT_DATA19 (PAO + VPS 数据库, 内置在 `/opt/openmx3.9/DFT_DATA19/`)
- 编译器: GNU GCC/G++/Gfortran 11
- MPI: OpenMPI 4.1.2
- 数学库: FFTW3, ScaLAPACK (OpenMPI), OpenBLAS, LAPACK
- ELPA 2018.05.001 (特征值求解器, 源码自带)

## 容器内容 (Intel 版)

- 基础系统: Ubuntu 24.04 (intel/oneapi-hpckit)
- 编译器: Intel ICX 2025.0 + IFX 2025.0
- MPI: IntelMPI 2021.14
- 数学库: Intel MKL 2025.0 (含 ScaLAPACK, BLACS, FFTW 接口)

## 使用方式

### 基本用法

```bash
# 必须用相对路径传参! 见 ⚠️ 注意事项
cd /path/to/workdir

# GNU 版
singularity run /mnt/shared/openmx3.9.sif input.dat
singularity exec /mnt/shared/openmx3.9.sif openmx input.dat

# Intel 版
singularity exec /mnt/shared/openmx3.9_intel.sif \
  mpirun -np 4 /opt/openmx3.9/work/openmx input.dat
```

### MPI 并行

```bash
# GNU 版 (容器内外 mpirun 均可)
mpirun -np 4 singularity exec /mnt/shared/openmx3.9.sif openmx input.dat
singularity exec /mnt/shared/openmx3.9.sif mpirun -np 4 openmx input.dat

# Intel 版 (必须用容器内 mpirun, 与宿主 MPI 不兼容)
singularity exec /mnt/shared/openmx3.9_intel.sif \
  mpirun -np 4 /opt/openmx3.9/work/openmx input.dat
```

### Slurm 提交

```bash
#!/bin/bash
#SBATCH -p 6138
#SBATCH -N 1
#SBATCH -n 40
#SBATCH -t 0:10:00

ulimit -s unlimited
cd /path/to/data          # ← 关键: 先用相对路径

# GNU
mpirun -np 40 singularity exec /mnt/shared/openmx3.9.sif openmx input.dat

# Intel
singularity exec /mnt/shared/openmx3.9_intel.sif \
  mpirun -np 40 /opt/openmx3.9/work/openmx input.dat
```

## ⚠️ 重要: 必须使用相对路径传参

OpenMX 3.9 存在一个 bug:
`Make_InputFile_with_FinalCoord.c:92-94`:

```c
sprintf(fname1, "%s%s#", filepath, file);  // "./" + argv[1] + "#"
fp1 = fopen(fname1, "w");                   // 路径错误 → NULL
fseek(fp1, 0, SEEK_END);                    // NULL → segfault
```

当 `argv[1]` 是绝对路径 (如 `/mnt/shared/xxx/input.dat`) 时, `fname1` 变成
`./mnt/shared/xxx/input.dat#`, 路径不存在。`fopen` 返回 NULL 未被检查,
`fseek` 在 NULL 上 segfault。

Intel 版在 40 核时连锁引发 OOM: rank 0 先崩, MPI 通信断裂, 剩余进程变僵尸被 OOM kill。

**解决办法**:

```bash
cd /path/to/data && singularity exec ... openmx input.dat     # ✅
singularity exec ... openmx /path/to/data/input.dat            # ❌ segfault!
```

## 环境变量

- `OPENMX_DFT_DATA_PATH=/opt/openmx3.9/DFT_DATA19` — 自动设置
- `OMP_NUM_THREADS=1` — OpenMX 不支持 OpenMP 多线程
- `PATH` 包含 `/opt/openmx3.9/work` 和 `/opt/openmx3.9/source`

## 编译配置

### GNU 版

```makefile
CC = mpicc -O3 -ffast-math -fopenmp -fcommon -Dkcomp
     -I/usr/include -I/usr/lib/x86_64-linux-gnu/openmpi/include
FC = mpif90 -O3 -ffast-math -fopenmp -fallow-argument-mismatch -Dkcomp
LIB = -lfftw3 -lmpi -lmpi_mpifh -lscalapack-openmpi -llapack -lblas -lgfortran
```

### Intel 版

```makefile
MKLROOT = /opt/intel/oneapi/mkl/2025.0
CC = mpiicx -Wno-implicit-function-declaration -fcommon -O3 -march=native \
     -qopenmp -I${MKLROOT}/include/fftw -Dkcomp
FC = mpiifx -O3 -march=native -qopenmp -Dkcomp
LIB = -L${MKLROOT}/lib/intel64 -lmkl_scalapack_lp64 -lmkl_intel_lp64 \
      -lmkl_intel_thread -lmkl_core -lmkl_blacs_intelmpi_lp64 \
      -liomp5 -lpthread -lm -ldl -lifcore
```

链接额外加 `-Wl,--allow-multiple-definition`。

## 性能对比

### 小体系: 8 Si 原子, 4×4×4 k-grid, 29 SCF

| MPI | GNU (6138 @ 2.0GHz) | Intel (6138 @ 2.0GHz) | Intel vs GNU |
|---|---|---|---|
| 1 | ~93 s (7940x 本地) | ~76 s (7940x 本地) | **快 18%** |
| 8 | 16.44 s | 16.43 s | 持平 |
| 16 | 16.76 s | 16.06 s | 快 4% |
| 24 | 18.15 s | 17.98 s | 持平 |
| 32 | 19.03 s | 16.16 s | 快 15% |
| 40 | 18.69 s | **17.42 s** | 快 7% |

注意: 8 原子 64 k-points 体系太小, >8 核后通信开销主导, 无加速。大体系 (16-32 原子 +
6×6×6 k-grid) 预期能体现更好的并行效率。

### 与 molcas_26.sif 一致性

| 项目 | openmx3.9.sif | molcas_26.sif |
|---|---|---|
| 版本 | 3.9.9 | 3.9.9 |
| 能量 Si 2-atom | -2.420862463494 Ha | -2.420862463494 Ha |
| SCF 路径 | 一致 | 一致 |
| DFT_DATA19 | 内置 `/opt/openmx3.9/DFT_DATA19` | 需挂载宿主的 |

## 构建问题与解决

### 1. Docker Hub DNS 无法解析
- 系统 DNS 无法解析 Docker Hub
- 用 `docker save` + `docker-archive` 绕过

### 2. Singularity docker-archive + fakeroot 无法 %post
- Singularity 4.1.0 处理 OCI 格式时有 bug
- 两步构建: 基础 SIF → sandbox → 手动操作 → 打包 SIF

### 3. OpenMX 不支持环境变量找 DFT_DATA19
- 修改 `Input_std.c:100`, 加 `getenv("OPENMX_DFT_DATA_PATH")` 支持
- 优先级: 环境变量 > 输入文件 DATA.PATH > 默认 ../DFT_DATA19

### 4. 绝对路径 segfault
- 见 ⚠️ 注意事项。已定位到 `Make_InputFile_with_FinalCoord.c`
- 长期应修源码加 NULL 检查, 但已确认用相对路径可规避

### 5. Intel 40 核 OOM
- 与问题4同一根因, 路径修复后也正常

## 重建步骤

```bash
# GNU 版
docker save ubuntu:22.04 -o /tmp/ubuntu_22.04.tar
singularity build --fakeroot /tmp/ubuntu_base.sif docker-archive:/tmp/ubuntu_22.04.tar
singularity build --fakeroot --sandbox /tmp/sandbox /tmp/ubuntu_base.sif
singularity exec --fakeroot --writable /tmp/sandbox bash -c '
  apt-get update && apt-get install -y build-essential gcc g++ gfortran make \
    openmpi-bin libopenmpi-dev libfftw3-dev libscalapack-openmpi-dev \
    libopenblas-dev liblapack-dev
  mkdir -p /opt/openmx3.9 && cp -r /path/to/source /opt/openmx3.9/source
  cp -r /path/to/DFT_DATA19 /opt/openmx3.9/DFT_DATA19
  cd /opt/openmx3.9/source && make clean && make -j$(nproc) openmx
  mkdir -p /opt/openmx3.9/work && cp openmx /opt/openmx3.9/work/
'
singularity build --force /mnt/shared/openmx3.9.sif /tmp/sandbox
```
