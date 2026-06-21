# OpenMX Container & 计算手册数据库

本工作区包含 OpenMX 3.9 / 4.0 的 Singularity 容器构建文件、Slurm 作业模板、测试算例、官方文档/教程资源，以及一个全文可搜索的**计算手册数据库**。

---

## 目录结构

| 目录/文件 | 说明 |
|-----------|------|
| `tuning_guide.md` | **性能调优索引** — 并行、SCF 收敛、大体系、benchmark、内存，附 `omx-db rag` 快捷命令 |
| `openmx.db` | **计算手册数据库** (SQLite + FTS5 + embedding, 3.4 MB) — 见下方用法 |
| `omx-db` | 命令行查询脚本 (搜索/语义/RAG/关键词) |
| `build/` | 容器构建记录 + Singularity 定义文件 (.def) |
| `slurm_scripts/` | Slurm 作业提交脚本 (GNU / Intel, v3.9 / v4.0) |
| `examples/` | 测试输入文件 (Si8.dat, Si16.dat) |
| `workshop/` | 2020 Hands-on 教程 PDF (6 份) |
| `video_lec/` | 视频讲座幻灯片 PDF (含 YouTube 链接) |
| `RESOURCES.md` | 下载资源清单 (含在线资源链接) |
| `benchmark_results.md` | 性能基准测试数据 |
| `openmx3.9_manual.pdf` | v3.9 手册 (16 MB) |
| `patch4.0.1.tar.gz` | v4.0 → 4.0.1 官方补丁 |
| `patch3.9.9.tar.gz` | v3.9 → 3.9.9 补丁 |
| `adpack2.2_source.tar.gz` | ADPACK 2.2 源码 |
| `openmx4.0.tar.gz` | OpenMX 4.0 源码 (182 MB) |
| `OpenMX_Viewer_offline.zip` | OpenMX Viewer 离线包 |

---

## 计算手册数据库 (`openmx.db`)

将 OpenMX v4.0 官方 HTML 手册 (83 节, 263 页) 的全文、目录结构、关键字索引以及所有 PDF 文档的元数据整合为 SQLite 数据库，支持 FTS5 全文搜索。

### 表结构

| 表 | 行数 | 说明 |
|----|------|------|
| `sections` | 281 | 手册章节/子节/子子节 (含编号、标题、文件路径) |
| `section_content` | 281 | 每节的原始文本 (用于 FTS 索引) |
| `index_entries` | 799 | 手册索引关键词 → 章节映射 (295 个唯一关键词) |
| `files` | 282 | 所有资源文件元数据 (263 HTML + 19 PDF) |
| `sections_fts` | 281 | FTS5 全文搜索虚表 (sec_num + title + raw_text) |

### 检索方式

| 命令 | 检索方式 | 适用场景 |
|------|----------|----------|
| `omx-db search "关键词"` | FTS5 全文搜索 | 精确关键词匹配 |
| `omx-db rag "自然语言描述"` | 语义搜索 (embedding) | 模糊匹配、概念检索 |
| `omx-db keyword "关键词"` | 手册索引查询 | 输入关键词查找出处 |
| `omx-db section 16` | 查看章节内容 | 精读某节 |

```bash
# 全文搜索 (FTS5, BM25 排序)
python3 omx-db search "NEGF transport"
python3 omx-db search "SCF convergence"

# 语义搜索 (RAG, 向量相似度)
python3 omx-db rag "how to tune SCF convergence in metallic systems"
python3 omx-db rag "parallel efficiency large scale calculation"

# 关键词索引查询 (手册后附 Index)
python3 omx-db keyword "Band.kpath"
python3 omx-db keyword "Atoms.SpeciesAndCoordinates"

# 查看指定章节
python3 omx-db section 16          # §16 SCF convergence
python3 omx-db section 46.3        # §46.3 Step 2: NEGF calculation
python3 omx-db section 47.1.1      # §47.1.1 PAO guiding functions

# 列出所有章节
python3 omx-db list

# 列出索引文件
python3 omx-db files
python3 omx-db files --type pdf    # 只看 PDF
python3 omx-db files --type html   # 只看 HTML

# 数据库统计
python3 omx-db stats
```

### 直接 SQL 查询示例

```bash
sqlite3 openmx.db
```

```sql
-- 按关键词搜索
SELECT s.sec_num, s.title FROM sections s
JOIN index_entries ie ON ie.file_path = s.file_path
WHERE ie.keyword = 'Calc.Type';

-- FTS5 全文搜索
SELECT sec_num, title, rank
FROM sections_fts
WHERE sections_fts MATCH '"DFT+U" OR "Hubbard"'
ORDER BY rank
LIMIT 10;

-- 查看章节 PDF 资源
SELECT path, category, size_bytes FROM files WHERE file_type = 'pdf';

-- 获取某节内容长度
SELECT s.sec_num, s.title, LENGTH(sc.raw_text) AS char_count
FROM sections s
JOIN section_content sc ON sc.section_id = s.id
ORDER BY char_count DESC
LIMIT 10;
```

---

## 容器构建

| 容器 | 路径 | 编译器 | 大小 |
|------|------|--------|------|
| GNU v3.9 | `/mnt/shared/openmx3.9.sif` | GCC 11 + OpenBLAS | 417 MB |
| Intel v3.9 | `/mnt/shared/openmx3.9_intel.sif` | ICX 2025 + MKL | 4.1 GB |
| Intel v4.0 | `/mnt/shared/openmx4.0_intel.sif` | IFX 2026 + MKL | 2.6 GB |

详情见 `build/` 目录下的构建笔记。

### 快速使用

```bash
cd /path/to/workdir

# v3.9 GNU
singularity exec /mnt/shared/openmx3.9.sif openmx Si8.dat

# v3.9 Intel (必须用容器内 mpirun)
singularity exec /mnt/shared/openmx3.9_intel.sif \
  mpirun -np 4 /opt/openmx3.9/work/openmx Si8.dat

# v4.0 Intel
singularity exec /mnt/shared/openmx4.0_intel.sif \
  /openmx4.0/work/openmx input.dat
```

### ⚠️ 注意事项

- **v3.9**: 必须用相对路径传参 (`cd data && openmx input.dat`)，绝对路径导致 segfault
- **v4.0**: 必须从可写目录运行 (SIF 只读, `setvbuf` on NULL 会崩溃)
- **Intel 版**: 必须用容器内 mpirun (Intel MPI 与宿主 OpenMPI 不兼容)

---

## 资源文件说明

| 类别 | 目录 | 文件数 | 内容 |
|------|------|--------|------|
| 手册 | `openmx4.0_manual/` | 263 HTML | v4.0 官方手册全文, 83 节 |
| 技术文档 | `docs/` | 6 PDF | 编译指南, 技术笔记, Viewer 手册等 |
| Workshop | `workshop/` | 6 PDF | 2020 Hands-on 教程 |
| 视频讲座 | `video_lec/` | 6 PDF | 含对应 YouTube 链接 |
| 补丁 | 根目录 | 2 tar.gz | 3.9→3.9.9, 4.0→4.0.1 |
| 源码 | 根目录 | 2 tar.gz + 1 zip | OpenMX 4.0, ADPACK 2.2, Viewer |

完整清单见 `RESOURCES.md`。

---

## 输入文件生成 (`omx-gen`)

从结构文件（CIF/XYZ/POSCAR）自动生成 OpenMX `.dat` 输入文件：

```bash
# SCF 计算（晶体）
omx-gen Si.cif -t scf_band -o Si.dat

# 金属体系（Kerker 混合，高 smearing）
omx-gen POSCAR -t scf_band_metal --cutoff 400 -k 8 8 8

# 分子/团簇（无 k 点）
omx-gen h2o.xyz -t scf_cluster

# 几何优化
omx-gen structure.cif -t geom_opt -o opt.dat

# 查看模板与关键词
omx-gen --list-templates
omx-gen --keyword scf.EigenvalueSolver
```

### 完整 pipeline：生成 → 提交 → 计算

```bash
# 1. 生成输入文件
omx-gen Si.cif -t scf_band -k 2 2 2 -o Si.dat

# 2. 通过 crisp 提交到集群
crisp submit                     # 自动检测计算器类型
crisp submit --calculator openmx # 或指定计算器

# 3. 查看作业状态
crisp jobs
crisp logs -n <task_name> -f     # 实时日志

# 结果自动拉回本地 output/ 目录
```

### 模板预设

| 模板 | 适用场景 | 自动 k 点 |
|------|----------|-----------|
| `scf_band` | 晶体 SCF，能带对角化 | ✅ |
| `scf_band_metal` | 金属体系（Kerker，高 smearing） | ✅ |
| `scf_cluster` | 分子/团簇（无 k 点） | ❌ |
| `geom_opt` | 几何优化 | ✅ |
| `band_dispersion` | 后 SCF 能带计算 | ❌ |

### 关键词知识库

`schemas/keywords.json` 包含 304 条结构化关键词信息：

- 93 条来自 ASE 的类型标注（integer/float/string/bool/tuple/matrix）
- 38 条来自 v3.9 手册的默认值
- 71 条来自 v4.0 §8.2 的描述文本
- 174 条骨架条目（专业章节，待补充）

```bash
# 通过 omx-db 查询结构化关键词
omx-db keyword --json scf.Kgrid
omx-db keyword --json scf.EigenvalueSolver
```
