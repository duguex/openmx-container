"""omx-gen — OpenMX input file generator."""

import argparse
import json
import os
import sys
from pathlib import Path

PKG_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = PKG_DIR / "schemas" / "keywords.json"
TEMPLATES_PATH = PKG_DIR / "schemas" / "templates.json"


def load_json(path, name):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: {name} not found at {path}", file=sys.stderr)
        sys.exit(1)


def auto_kgrid(atoms, kspacing):
    import numpy as np
    cell = atoms.cell
    recip = cell.reciprocal() * (2 * np.pi)
    lengths = np.linalg.norm(recip, axis=1)
    return [max(1, int(np.floor(l / kspacing))) for l in lengths]


def to_ase_key(openmx_key, schema):
    if openmx_key in schema:
        entry = schema[openmx_key]
        if entry.get("ase_key"):
            return entry["ase_key"]
    parts = openmx_key.split(".")
    return "_".join(parts).lower()


def generate_input(structure_path, template_name, overrides, schema,
                   templates, kspacing, dry_run, verbose, output_path,
                   json_output=False):
    from ase.io import read
    from ase.calculators.openmx import OpenMX

    if verbose:
        print(f"Reading structure: {structure_path}", file=sys.stderr)
    try:
        atoms = read(structure_path)
    except Exception as e:
        die_json(f"reading structure file '{structure_path}': {e}", json_output=json_output)

    if verbose:
        print(f"  Atoms: {len(atoms)}, formula: {atoms.get_chemical_formula()}",
              file=sys.stderr)

    if template_name not in templates:
        die_json(f"unknown template '{template_name}'. "
                 f"Available: {', '.join(sorted(templates.keys()))}", json_output=json_output)

    template = templates[template_name]
    params = dict(template["keywords"])

    if verbose:
        print(f"Using template: {template_name} — "
              f"{template.get('description', '')}", file=sys.stderr)

    # Auto k-points
    if template.get("auto_kpoints") and "kpts" not in overrides:
        kgrid = auto_kgrid(atoms, kspacing)
        params["kpts"] = tuple(kgrid)
        if verbose:
            print(f"  Auto kpts: {tuple(kgrid)} (kspacing={kspacing} 1/Å)",
                  file=sys.stderr)

    # Apply overrides
    for key, value in overrides.items():
        params[key] = value
        if verbose:
            print(f"  Override: {key} = {value}", file=sys.stderr)

    # Resolve None defaults from schema
    for key in list(params.keys()):
        if params[key] is None:
            for omx_k, entry in schema.items():
                if entry.get("ase_key") == key and entry.get("default") is not None:
                    params[key] = entry["default"]
                    if verbose:
                        print(f"  Schema default: {key} = {entry['default']}",
                              file=sys.stderr)
                    break

    # Resolve DATA.PATH
    if "data_path" not in params or not params.get("data_path"):
        env_path = os.environ.get("OPENMX_DFT_DATA_PATH")
        if env_path:
            params["data_path"] = env_path
            if verbose:
                print(f"  Using OPENMX_DFT_DATA_PATH: {env_path}", file=sys.stderr)
        else:
            die_json("DATA.PATH not set. Set OPENMX_DFT_DATA_PATH to your DFT_DATA19 "
                     "directory (e.g. /mnt/shared/DFT_DATA19).", json_output=json_output)

    data_path = params["data_path"]
    vps_dir = os.path.join(data_path, "VPS")
    if not os.path.isdir(vps_dir):
        die_json(f"VPS directory not found at {vps_dir}", json_output=json_output)

    # Generate output stem
    if output_path:
        stem = Path(output_path).stem
    else:
        stem = Path(structure_path).stem

    # Write input
    if dry_run:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            calc = OpenMX(label=os.path.join(tmpdir, stem),
                          command="", **params)
            calc.write_input(atoms)
            dat_path = os.path.join(tmpdir, f"{stem}.dat")
            with open(dat_path) as f:
                content = f.read()
        content = "\n".join(
            l for l in content.split("\n")
            if not l.strip().startswith("System.CurrentDirectory")
        )
        sys.stdout.write(content)
        if verbose:
            print("(dry-run: printed to stdout)", file=sys.stderr)
    else:
        out_path = output_path or f"{stem}.dat"
        calc = OpenMX(label=os.path.join(os.getcwd(), stem),
                      command="", **params)
        calc.write_input(atoms)
        written = f"{stem}.dat"
        if os.path.abspath(written) != os.path.abspath(out_path):
            os.rename(written, out_path) if os.path.exists(written) else None
        # Strip System.CurrentDirectory
        with open(out_path) as f:
            lines = f.readlines()
        kept = [l for l in lines if not l.strip().startswith("System.CurrentDirectory")]
        if len(kept) != len(lines):
            with open(out_path, "w") as f:
                f.writelines(kept)
        if verbose:
            print(f"Written: {out_path}", file=sys.stderr)

    return params


def lookup_templates_json(templates):
    """Return templates as JSON-serializable list of dicts."""
    return [
        {"name": name, "description": t.get("description"),
         "auto_kpoints": t.get("auto_kpoints"),
         "requires_prior_scf": t.get("requires_prior_scf"),
         "keywords": t["keywords"]}
        for name, t in sorted(templates.items())
    ]


def lookup_keywords_json(schema):
    """Return keyword schema as JSON-serializable list, sorted by name."""
    return [{"name": k, **v} for k, v in sorted(schema.items())]


def die_json(msg, json_output=False, code=1):
    """Print JSON error and exit, or print text error and exit with code."""
    if json_output:
        print(json.dumps({"error": msg, "exit": code}))
        sys.exit(0)
    else:
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(code)



def cli():
    parser = argparse.ArgumentParser(
        description="Generate OpenMX .dat input files from structure + templates",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("structure", nargs="?",
                        help="Input structure file (CIF, XYZ, POSCAR, ...)")
    parser.add_argument("-t", "--template", default="scf_band",
                        help="Calculation template (default: scf_band)")
    parser.add_argument("-o", "--output", help="Output .dat file")
    parser.add_argument("--list-templates", action="store_true",
                        help="List available templates")
    parser.add_argument("--list-keywords", action="store_true",
                        help="List all known keywords with type info")
    parser.add_argument("--type",
                        help="Filter by type (string, integer, float, bool, tuple_integer, tuple_float, matrix)")
    parser.add_argument("--keyword", metavar="KEY",
                        help="Show structured metadata for a single keyword")
    parser.add_argument("-k", "--kpoints", type=int, nargs=3,
                        metavar=("NX", "NY", "NZ"),
                        help="Override k-point grid")
    parser.add_argument("--kspacing", type=float, default=0.33,
                        help="k-point spacing in 1/Å (default: 0.33)")
    parser.add_argument("-x", "--xc",
                        help="Override XC functional (PBE, LDA, etc.)")
    parser.add_argument("--spin", help="Override spin: Off | On | NC")
    parser.add_argument("--cutoff", type=float,
                        help="Override energy cutoff (eV)")
    parser.add_argument("-s", "--set", action="append", default=[],
                        metavar="KEY=VALUE",
                        help="Set an arbitrary OpenMX keyword")
    parser.add_argument("-d", "--dry-run", action="store_true",
                        help="Print to stdout instead of writing file")
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show keyword resolution")
    parser.add_argument("-j", "--json", action="store_true",
                        help="JSON output (machine-readable)")

    args = parser.parse_args()
    schema = load_json(SCHEMA_PATH, "keywords.json")
    templates = load_json(TEMPLATES_PATH, "templates.json")

    if args.list_templates:
        if args.json:
            print(json.dumps(lookup_templates_json(templates), indent=2, ensure_ascii=False))
        else:
            print("Available templates:")
            for name, t in sorted(templates.items()):
                auto = " [auto-kpoints]" if t.get("auto_kpoints") else ""
                prior = " [requires prior SCF]" if t.get("requires_prior_scf") else ""
                desc = t.get("description", "")
                print(f"  {name}{auto}{prior}")
                if desc:
                    print(f"        {desc}")
                for key, val in t["keywords"].items():
                    val_str = json.dumps(val) if val is not None else "auto"
                    print(f"          {key} = {val_str}")
        return

    if args.list_keywords:
        if args.json:
            kw_list = lookup_keywords_json(schema)
            if args.type:
                kw_list = [e for e in kw_list if e.get("type") == args.type]
            print(json.dumps(kw_list, indent=2, ensure_ascii=False))
        else:
            print("Known keywords:")
            for kw, entry in sorted(schema.items()):
                if entry["type"]:
                    print(f"  {kw}  [{entry['type']}]", end="")
                    if entry.get("default"):
                        print(f"  default={entry['default']}", end="")
                    if entry.get("unit"):
                        print(f"  ({entry['unit']})", end="")
                    print()
                else:
                    print(f"  {kw}  [untyped — manual section keyword]")
        return

    if args.keyword:
        kw = args.keyword
        if kw not in schema:
            if args.json:
                print(json.dumps({"error": f"Keyword '{kw}' not found in schema"}))
                sys.exit(1)
            print(f"Keyword '{kw}' not found in schema.", file=sys.stderr)
            sys.exit(1)
        if args.json:
            print(json.dumps(schema[kw], indent=2, ensure_ascii=False))
        else:
            entry = schema[kw]
            print(f"{kw}:")
            print(f"  type:        {entry.get('type', 'null')}")
            print(f"  ase_key:     {entry.get('ase_key', 'null')}")
            print(f"  default:     {json.dumps(entry.get('default'))}")
            print(f"  valid:       {json.dumps(entry.get('valid_values'))}")
            print(f"  unit:        {json.dumps(entry.get('unit'))}")
            print(f"  section:     {entry.get('section', 'null')}")
            print(f"  source:      {entry.get('source', 'null')}")
            if entry.get("description"):
                print(f"  description: {entry['description']}")
        return

    if not args.structure:
        die_json("STRUCTURE file is required. Use --help for usage.", json_output=args.json)

    if not os.path.isfile(args.structure):
        die_json(f"structure file '{args.structure}' not found", json_output=args.json)

    overrides = {}
    for arg in args.set:
        if "=" not in arg:
            print(f"Warning: --set '{arg}' missing '=', skipping", file=sys.stderr)
            continue
        key, _, raw_val = arg.partition("=")
        ase_key = to_ase_key(key.strip(), schema)
        raw_val = raw_val.strip()
        try:
            val = float(raw_val) if ("." in raw_val or "e" in raw_val.lower()) else int(raw_val)
        except (ValueError, TypeError):
            val = raw_val
        overrides[ase_key] = val

    if args.kpoints:
        overrides["kpts"] = tuple(args.kpoints)
    if args.xc:
        overrides["scf_xctype"] = args.xc
    if args.spin:
        overrides["scf_spinpolarization"] = args.spin
    if args.cutoff:
        overrides["energy_cutoff"] = args.cutoff

    generate_input(
        structure_path=args.structure,
        template_name=args.template,
        overrides=overrides,
        schema=schema,
        templates=templates,
        kspacing=args.kspacing,
        dry_run=args.dry_run,
        verbose=args.verbose,
        output_path=args.output,
        json_output=args.json,
    )


if __name__ == "__main__":
    cli()
