"""omx-db — OpenMX manual database query tool."""

import json
import re
import os
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = PKG_DIR.parent
DB_PATH = PROJECT_ROOT / "openmx.db"


def strip_ansi(text):
    """Strip ANSI escape sequences from text."""
    return re.sub(r'\x1b\[[0-9;]*m', '', text)


def get_db():
    if not os.path.exists(DB_PATH):
        print(f"Error: database not found at {DB_PATH}", file=sys.stderr)
        sys.exit(1)
    db = sqlite3.connect(str(DB_PATH))
    db.row_factory = sqlite3.Row
    return db


def cmd_search(args, json_output=False):
    query = " ".join(args)
    if not query:
        if json_output:
            print(json.dumps({"error": "No query provided"}))
        else:
            print("Usage: omx-db search <query>")
        return
    db = get_db()
    fts_query = " OR ".join(f'"{w}"' if " " in w else w for w in query.split())
    rows = db.execute("""
        SELECT rowid, sec_num, title, rank,
               snippet(sections_fts, 2, '\033[33m', '\033[0m', '...', 50) AS ctx
        FROM sections_fts
        WHERE sections_fts MATCH ?
        ORDER BY rank
        LIMIT 20
    """, (fts_query,)).fetchall()
    if not rows:
        if json_output:
            print(json.dumps({"results": [], "count": 0, "query": query}))
        else:
            print(f"No results for: {query}")
        return
    if json_output:
        print(json.dumps({
            "results": [
                {"sec_num": r["sec_num"], "title": r["title"],
                 "rank": r["rank"], "snippet": strip_ansi(r["ctx"])}
                for r in rows
            ],
            "count": len(rows),
            "query": query
        }, indent=2, ensure_ascii=False))
    else:
        print(f'\033[32m🔍 {len(rows)} results for "{query}"\033[0m\n')
        for r in rows:
            sec = f'§{r["sec_num"]}' if r["sec_num"] else ""
            print(f'  \033[36m{sec:>12s}\033[0m  \033[1m{r["title"]}\033[0m')
            print(f'  {r["ctx"]}')
            print()
    db.close()


def cmd_keyword(args, json_output=False):
    keyword = " ".join(args)
    if not keyword:
        if json_output:
            print(json.dumps({"error": "No keyword provided"}))
        else:
            print("Usage: omx-db keyword <keyword>")
        return
    # Try exact schema lookup first
    if json_output:
        schema_path = PKG_DIR / "schemas" / "keywords.json"
        if schema_path.exists():
            with open(schema_path) as f:
                schema = json.load(f)
            if keyword in schema:
                print(json.dumps(schema[keyword], indent=2, ensure_ascii=False))
                return
    # DB fallback
    db = get_db()
    rows = db.execute("""
        SELECT DISTINCT ie.keyword,
               COALESCE(s.sec_num, '') AS sec_num,
               COALESCE(s.title, '') AS title,
               ie.file_path
        FROM index_entries ie
        LEFT JOIN sections s ON s.file_path = ie.file_path
            AND (s.anchor = '' OR ie.anchor = '' OR s.anchor = ie.anchor)
        WHERE ie.keyword LIKE ?
        ORDER BY ie.keyword, s.sec_num
        LIMIT 30
    """, (f"%{keyword}%",)).fetchall()
    if not rows:
        if json_output:
            print(json.dumps({"results": [], "count": 0}))
            return
        print(f'No index keywords matching "{keyword}". Trying full-text search...\n')
        cmd_search(args)
        return
    if json_output:
        print(json.dumps({
            "results": [
                {"keyword": r["keyword"], "sec_num": r["sec_num"],
                 "title": r["title"], "file": r["file_path"]}
                for r in rows
            ],
            "count": len(rows)
        }, indent=2, ensure_ascii=False))
    else:
        print(f'\033[32m📖 {len(rows)} keyword results for "{keyword}"\033[0m\n')
        cur_kw = None
        for r in rows:
            if r["keyword"] != cur_kw:
                cur_kw = r["keyword"]
                print(f'  \033[1m{cur_kw}\033[0m')
            ref = f'§{r["sec_num"]}' if r["sec_num"] else ""
            print(f'    {ref:>12s}  → {r["file_path"]}')
        print()
    db.close()


def cmd_section(args, json_output=False):
    num = " ".join(args)
    if not num:
        if json_output:
            print(json.dumps({"error": "No section number provided"}))
        else:
            print('Usage: omx-db section <num>  (e.g. "16", "8.2", "46.4.3")')
        return
    db = get_db()
    row = db.execute("""
        SELECT s.sec_num, s.title, s.file_path, s.depth,
               SUBSTR(sc.raw_text, 1, 2000) AS excerpt
        FROM sections s
        JOIN section_content sc ON sc.section_id = s.id
        WHERE s.sec_num = ?
    """, (num,)).fetchone()
    if not row:
        rows = db.execute("""
            SELECT sec_num, title FROM sections
            WHERE sec_num LIKE ? OR title LIKE ?
            LIMIT 5
        """, (f"{num}%", f"%{num}%")).fetchall()
        if json_output:
            suggestions = [{"sec_num": r["sec_num"], "title": r["title"]} for r in rows] if rows else []
            print(json.dumps({"error": f"Section not found: {num}", "suggestions": suggestions}, indent=2, ensure_ascii=False))
        else:
            if rows:
                print("Did you mean?")
                for r in rows:
                    print(f'  §{r["sec_num"]:>8s}  {r["title"]}')
            else:
                print(f"Section not found: {num}")
        return
    if json_output:
        print(json.dumps({
            "sec_num": row["sec_num"],
            "title": row["title"],
            "file": row["file_path"],
            "depth": row["depth"],
            "content": row["excerpt"]
        }, indent=2, ensure_ascii=False))
    else:
        print(f'\033[36m§{row["sec_num"]}\033[0m  \033[1m{row["title"]}\033[0m')
        print(f'  File: \033[33m{row["file_path"]}\033[0m')
        print(f'  URL:  \033[33mopenmx4.0_manual/{row["file_path"]}\033[0m')
        print(f"  Depth: {row['depth']}")
        print()
        print("─" * 60)
        excerpt = row["excerpt"][:2000]
        for line in textwrap.wrap(excerpt, width=78):
            print(f"  {line}")
        print("─" * 60)
    db.close()


def cmd_list(args, json_output=False):
    db = get_db()
    rows = db.execute("""
        SELECT sec_num, title, depth FROM sections
        WHERE depth <= 2
        ORDER BY
            CAST(SUBSTR('00' || sec_num, 1, 2) AS INTEGER),
            SUBSTR(sec_num, INSTR(sec_num, '.') + 1) * 1
    """).fetchall()
    if json_output:
        print(json.dumps({
            "sections": [
                {"sec_num": r["sec_num"], "title": r["title"], "depth": r["depth"]}
                for r in rows
            ]
        }, indent=2, ensure_ascii=False))
    else:
        print("\033[32m📑 Manual Contents\033[0m\n")
        for r in rows:
            indent = "  " * (r["depth"] - 1) if r["sec_num"] else ""
            sec = f'§{r["sec_num"]}' if r["sec_num"] else ""
            print(f'  {indent}\033[36m{sec:>12s}\033[0m  {r["title"]}')
        print()
    db.close()


def cmd_files(args, json_output=False):
    file_type = None
    if "--type" in args:
        idx = args.index("--type")
        file_type = args[idx + 1]
        args = args[:idx] + args[idx + 2 :]
    db = get_db()
    if file_type:
        rows = db.execute("""
            SELECT path, file_type, size_bytes, category FROM files
            WHERE file_type = ?
            ORDER BY category, path
        """, (file_type,)).fetchall()
    else:
        rows = db.execute("""
            SELECT path, file_type, size_bytes, category FROM files
            ORDER BY file_type, category, path
        """).fetchall()
    if json_output:
        print(json.dumps({
            "files": [
                {"path": r["path"], "type": r["file_type"],
                 "category": r["category"], "size_bytes": r["size_bytes"]}
                for r in rows
            ]
        }, indent=2, ensure_ascii=False))
    else:
        print(f"\033[32m📁 {len(rows)} files\033[0m\n")
        for r in rows:
            sz = f'{r["size_bytes"]/1024:.0f} KB' if r["size_bytes"] < 1024 * 1024 else f'{r["size_bytes"]/(1024*1024):.1f} MB'
            print(f'  [{r["category"]:10s}] [{r["file_type"]:4s}] {r["path"]:50s} {sz:>8s}')
        print()
    db.close()


def cmd_stats(args, json_output=False):
    db = get_db()
    if json_output:
        table_counts = [(t, db.execute(f"SELECT COUNT(*) AS cnt FROM {t}").fetchone()["cnt"])
                        for t in ["sections", "index_entries", "section_content", "files", "sections_fts"]]
        cats = db.execute("SELECT category, COUNT(*) AS cnt FROM files GROUP BY category ORDER BY category").fetchall()
        types = db.execute("SELECT file_type, COUNT(*) AS cnt FROM files GROUP BY file_type").fetchall()
        db_size = os.path.getsize(str(DB_PATH))
        print(json.dumps({
            "tables": {t: cnt for t, cnt in table_counts},
            "files_by_category": {c["category"]: c["cnt"] for c in cats},
            "files_by_type": {t["file_type"]: t["cnt"] for t in types},
            "db_size_mb": round(db_size / (1024*1024), 1)
        }, indent=2, ensure_ascii=False))
    else:
        print("\033[32m📊 Database Statistics\033[0m\n")
        for table in ["sections", "index_entries", "section_content", "files", "sections_fts"]:
            cnt = db.execute(f"SELECT COUNT(*) AS cnt FROM {table}").fetchone()["cnt"]
            print(f"  {table:20s}  {cnt:>6d} rows")
        cats = db.execute("SELECT category, COUNT(*) AS cnt FROM files GROUP BY category ORDER BY category").fetchall()
        pad = " " * 20
        for c in cats:
            print(f"  {pad}  {c['category']:>10s}: {c['cnt']} files")
        types = db.execute("SELECT file_type, COUNT(*) AS cnt FROM files GROUP BY file_type").fetchall()
        for t in types:
            print(f"  {pad}  {t['file_type']:>10s}: {t['cnt']} files")
        db_size = os.path.getsize(str(DB_PATH))
        print(f"\n  DB file size: {db_size/(1024*1024):.1f} MB")
    db.close()


def cmd_rag(args, json_output=False):
    query = " ".join(args)
    if not query:
        if json_output:
            print(json.dumps({"error": "No query provided"}))
        else:
            print("Usage: omx-db rag <query>")
        return
    if not json_output:
        print("\033[2mLoading embedding model...\033[0m", flush=True)
    env = os.environ.copy()
    env["HF_HUB_OFFLINE"] = "1"
    env["TRANSFORMERS_OFFLINE"] = "1"
    script = """
import os, sys, sqlite3, json, numpy as np
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-small-en-v1.5', device='cpu')
q = sys.argv[1]
q_emb = model.encode(q, normalize_embeddings=True)
db = sqlite3.connect(sys.argv[2])
db.row_factory = sqlite3.Row
rows = db.execute('SELECT section_id, sec_num, title, file_path, embedding FROM section_embeddings').fetchall()
results = []
for r in rows:
    emb = np.frombuffer(r['embedding'], dtype=np.float32)
    sim = float(np.dot(q_emb, emb))
    results.append((sim, r['sec_num'], r['title'], r['file_path']))
results.sort(reverse=True)
print(json.dumps([{'sim': s, 'sec_num': n, 'title': t, 'file': f} for s,n,t,f in results[:10]]))
"""
    try:
        result = subprocess.run(
            [sys.executable, "-c", script, query, str(DB_PATH)],
            capture_output=True, text=True, timeout=120, env=env
        )
        if result.returncode != 0:
            if json_output:
                print(json.dumps({"error": result.stderr[:500]}))
            else:
                print(f"Error: {result.stderr[:500]}")
            return
        hits = json.loads(result.stdout.strip())
    except subprocess.TimeoutExpired:
        if json_output:
            print(json.dumps({"error": "embedding query timed out"}))
        else:
            print("Error: embedding query timed out")
        return
    except json.JSONDecodeError as e:
        if json_output:
            print(json.dumps({"error": f"Error parsing results: {e}"}))
        else:
            print(f"Error parsing results: {e}")
        return
    if not hits:
        if json_output:
            print(json.dumps({"results": [], "count": 0}))
        else:
            print("No results.")
        return
    if json_output:
        print(json.dumps(hits, indent=2, ensure_ascii=False))
    else:
        print(f'\033[32m🔍 Semantic search: "{query}"\033[0m\n')
        for h in hits:
            sec = f'§{h["sec_num"]}' if h["sec_num"] else ""
            bar_len = int(h["sim"] * 30)
            bar = "█" * bar_len + "░" * (30 - bar_len)
            print(f'  \033[36m{sec:>12s}\033[0m  \033[1m{h["title"]}\033[0m')
            print(f"  {bar}  {h['sim']:.3f}")
            print()
        print('  \033[2m(query took ~9s first call, model loaded in subprocess)\033[0m')


def cli():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    use_json = "--json" in sys.argv
    if use_json:
        sys.argv = [a for a in sys.argv if a != "--json"]
    cmd = sys.argv[1]
    args = sys.argv[2:]
    cmds = {
        "rag": cmd_rag,
        "search": cmd_search,
        "keyword": cmd_keyword,
        "section": cmd_section,
        "list": cmd_list,
        "files": cmd_files,
        "stats": cmd_stats,
    }
    if cmd in cmds:
        cmds[cmd](args, json_output=use_json)
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
