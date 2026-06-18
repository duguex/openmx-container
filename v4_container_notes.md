# OpenMX 4.0 Singularity 容器构建记录

## 最终产物

| 容器 | 路径 | 大小 | 基础镜像 | 编译器 |
|---|---|---|---|---|
| Intel v4.0 | `/mnt/shared/openmx4.0_intel.sif` | 2.6 GB | `dc1394/openmx4.0-ubuntu22.04:0.2` | IFX 2026 + MKL 2026 |

GNU 版已移除 (Cluster/Band 求解器返回 NaN, 无法修复)。

## 容器内容

- 基础系统: Ubuntu 22.04
- 编译器: Intel ICX 2026.0 (C), IFX 2026.0 (Fortran)
- MPI: Intel MPI 2021.18
- 数学库: Intel MKL 2026.0
- ELPA 2018.05.001
- OpenMX 源码位于 `/openmx4.0/source/`
- DFT_DATA19 位于 `/openmx4.0/DFT_DATA19`

## 使用方式

```bash
# 必须从可写目录运行! 见 ⚠️ 注意事项
cd /path/to/workdir

# 单进程
singularity exec /mnt/shared/openmx4.0_intel.sif \
  /openmx4.0/work/openmx input.dat

# MPI 并行 (必须用容器内的 mpirun)
singularity exec /mnt/shared/openmx4.0_intel.sif \
  mpirun -np 4 /openmx4.0/work/openmx input.dat
```

## ⚠️ 注意事项

### 必须从可写目录运行

SIF 内文件系统是只读 squashfs。OpenMX 会在 CWD 写输出文件 (如 `met.out`),
失败会 segfault (`setvbuf` on NULL)。**始终在可写目录运行**, 并把输入文件放在那里。

✅ `cd /scratch/workdir && singularity exec ... openmx input.dat`
❌ `singularity exec ... openmx /scratch/workdir/input.dat`

### `OPENMX_DFT_DATA_PATH` 自动发现

环境变量已设好 (`/openmx4.0/DFT_DATA19`), 输入文件不需要 `DATA.PATH`。

### 必须用容器内的 mpirun

容器内是 Intel MPI。宿主 MPI (OpenMPI) 与 Intel MPI 不兼容。
始终 `singularity exec ... mpirun -np N /openmx4.0/work/openmx input.dat`。

## 已应用的补丁

| 补丁 | 文件 | 说明 |
|---|---|---|
| Official 4.0.1 | `Band_DFT_Dosout.c`, `Mulliken_Charge.c`, `GaAs.dat` | 官方替换文件 |
| Patch A | `Input_std.c:100` | 添加 `getenv("OPENMX_DFT_DATA_PATH")` 支持, 含空字符串修复 |
| Patch B | `Make_InputFile_with_FinalCoord.c:117,646` | `fopen` 后加 NULL 检查, 防止只读目录 segfault |

## 已知问题

### Intel 版 Singularity 下 setvbuf segfault

SIF 内文件系统只读。OpenMX 在 CWD 创建输出文件时 `fopen` 返回 NULL,
后续 `setvbuf` 崩溃。Patch B 修复了部分路径, 但 `UCell_Box` 等处仍有类似问题。
**解决**: 从可写目录运行。

### Cluster/Band 求解器 (Intel 版)

参考镜像使用 IFX 2026 + MKL 2026, Cluster 求解器正常。
GNU 版因 `Cluster_DFT_Col.c` 被上游重写 (3011→4694 行) 引入数值问题,
返回 NaN, 已删除。

## 构建过程摘要

最终 SIF 基于 `dc1394/openmx4.0-ubuntu22.04:0.2`:
1. 启动容器, 安装 `make`
2. 应用 official 4.0.1 补丁, Patch A, Patch B
3. 增量编译 (保持预编译的 ELPA `.o` 不变, 只重编修改过的 `.c` 文件)
4. 添加 `.singularity.d/env/90-openmx-env.sh` (PATH, LD_LIBRARY_PATH, OPENMX_DFT_DATA_PATH)
5. `docker export` → 目录 → `singularity build` 成 SIF
