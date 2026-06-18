# OpenMX 官方资源清单

## 计算手册数据库

性能调优索引见 `tuning_guide.md` — 涵盖并行方案、SCF 收敛、大体系方法、benchmark、内存分析。


本工作区附带一个 SQLite 全文搜索数据库 `openmx.db`，将 v4.0 HTML 手册全部 83 节
(263 页) + 19 份 PDF 文档元数据索引化。使用方法见 `README.md` 或:
```bash
python3 omx-db search "关键词"
python3 omx-db keyword "关键词"
```

下载时间: 2026-06-16
总计: ~90 MB (已下载) + 大文件后台下载中

---

## 1. 用户手册

| 文件 | 大小 | 来源 |
|---|---|---|
| `openmx3.9_manual.pdf` | 17 MB | https://openmx-square.org/openmx_man3.9/openmx3.9.pdf |
| `docs/New_Features_OpenMX3.9.pdf` | 2.0 MB | 同上页面 |
| `docs/Viewer_Manual.pdf` | 13 MB | https://www.openmx-square.org/viewer/10th_Manual_OpenMX_Viewer.pdf |

HTML 版手册: https://openmx-square.org/openmx_man3.9/
v4.0 手册: https://openmx-square.org/openmx_man4.0/

## 2. 安装指南

| 文件 | 大小 | 来源 |
|---|---|---|
| `docs/OpenMX-Compile.pdf` | 655 KB | https://www.openmx-square.org/tech_notes/OpenMX-Compile.pdf |

## 3. 技术笔记

| 文件 | 大小 | 来源 |
|---|---|---|
| `docs/TechNotes_TotalEnergy.pdf` | 132 KB | https://www.openmx-square.org/tech_notes/tech1-1_3/tech1-1_3.pdf |
| `docs/Recursion_Methods.pdf` | 1.3 MB | https://www.openmx-square.org/recursion.pdf |

## 4. ADPACK 文档

| 文件 | 大小 |
|---|---|
| `docs/ADPACK_Manual.pdf` | 250 KB |
| `adpack2.2_source.tar.gz` | 352 KB |

## 5. Workshop 教程 (2020 Hands-on)

| 文件 | 大小 | 内容 |
|---|---|---|
| `workshop/OpenMX-General.pdf` | 3.2 MB | 通用教程 |
| `workshop/OpenMX-1.pdf` | 2.6 MB | 实操 Part 1 |
| `workshop/OpenMX-2.pdf` | 2.2 MB | 实操 Part 2 |
| `workshop/OpenMX-Geo.pdf` | 1.6 MB | 几何优化 |
| `workshop/OpenMX-XPS.pdf` | 536 KB | XPS 芯能级 |
| `workshop/OpenMX-NEGF.pdf` | 1.4 MB | NEGF 输运 |

## 6. 视频讲座 PDF (含 YouTube 链接)

| 文件 | 大小 | YouTube |
|---|---|---|
| `video_lec/OpenMX-Hands-on-2014Oct10.pdf` | 3.2 MB | https://youtu.be/-V0FcsT8mDI (Part 1-5) |
| `video_lec/OpenMX-Compile-2014Oct10.pdf` | 1.3 MB | https://youtu.be/w6B3rIJH4kc |
| `video_lec/OrderN-Part1.pdf` | 3.4 MB | https://youtu.be/yAix4FtocE8 |
| `video_lec/OrderN-Part2.pdf` | 3.7 MB | https://youtu.be/utBwqp8OPB0 |
| `video_lec/OpenMX-2015-Oct-15.pdf` | 2.2 MB | https://youtu.be/A901Iwj4Aw8 |
| `video_lec/OpenMX-2015-Oct-22.pdf` | 1.8 MB | https://youtu.be/8fiCLoGU_30 |

## 7. 补丁

| 文件 | 大小 | 说明 |
|---|---|---|
| `patch3.9.9.tar.gz` | 1.1 MB | OpenMX 3.9 → 3.9.9 补丁 (2021-10-17) |
| `patch4.0.1.tar.gz` | 31 KB | OpenMX 4.0 → 4.0.1 补丁 (2026-05-08) |

## 8. 源码 (后台下载中, 限时 1h)

| 文件 | 预计大小 | 来源 |
|---|---|---|
| `openmx3.8.tar.gz` | 136 MB (后台 bg_4) | https://www.openmx-square.org/openmx3.8.tar.gz |
| `openmx3.9.tar.gz` | 158 MB (后台 bg_5) | https://www.openmx-square.org/openmx3.9.tar.gz |
| `openmx4.0.tar.gz` | 182 MB (后台 bg_5) | https://www.openmx-square.org/openmx4.0.tar.gz |
| `OpenMX_Viewer_offline.zip` | 51 MB (后台 bg_5) | https://www.openmx-square.org/viewer/omxv1.76.zip |

## 9. 在线资源 (无需下载)

| 资源 | 链接 |
|---|---|
| OpenMX Viewer (WebGL) | https://www.openmx-square.org/viewer/ |
| 论坛 | https://www.openmx-square.org/forum/ |
| 出版物列表 | https://www.openmx-square.org/publications.html |
| VPS/PAO 2019 数据库 (按元素) | https://www.openmx-square.org/vps_pao2019/ |
| VPS/PAO 2026 数据库 | https://www.openmx-square.org/vps_pao2026/ |
| AB2 二维材料结构地图 | http://www.openmx-square.org/2d-ab2/ |
| 原子 LDA/HF 计算数据库 | http://www.openmx-square.org/atoms/ |
| SAMLAI 材料结构搜索 | http://www.samlai-square.org |
| OpenFFT | https://www.openmx-square.org/openfft/ |
| Exact Exchange 笔记 | https://www.openmx-square.org/exx/ |
| OpenMX GPU 版 (GitHub) | https://github.com/dc1394/openmx3.9.9_gpu |

## 10. 容器相关 (本工作区原有)

| 文件 | 说明 |
|---|---|
| `build_notes.md` | 容器构建记录 & 已知 bug |
| `slurm_scripts/run_gnu.sh` | Slurm GNU 版作业模板 |
| `slurm_scripts/run_intel.sh` | Slurm Intel 版作业模板 |
| `examples/Si8.dat` | 8 原子 Si 测试输入 |
| `examples/Si16.dat` | 16 原子 Si 输入 |
| `benchmark_results.md` | 性能测试结果 |

容器映像:
- GNU 版: `/mnt/shared/openmx3.9.sif` (417 MB)
- Intel 版: `/mnt/shared/openmx3.9_intel.sif` (4.1 GB)
- DFT_DATA19 数据库内置于容器 `/opt/openmx3.9/DFT_DATA19/`
