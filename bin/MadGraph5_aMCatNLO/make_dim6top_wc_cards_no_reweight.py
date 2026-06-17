#!/usr/bin/env python3
"""
Create dim6top fixed-WC ttbar production card directories without reweighting,
without MadSpin, and without any '_madspin' substring in generated names.

This version intentionally mimics the BSMRef card-maker style:
  - generated run_all_gridpacks.sh contains only one standalone gridpack command per line
  - no shared environment setup in the run-all file
  - SLURM jobs should set PRODHOME/SCRAM_ARCH/CMSSW_VERSION themselves

Important for the no-MadSpin debug campaign:
  - proc cards are generated from scratch as stable-top production only
  - no inline decays in proc_card
  - no *_madspin_card.dat is written
  - run cards remove any madspin/reweight menu lines entirely (MG5 2.6.5 cannot compile OFF = madspin/reweight)

Usage from genproductions/bin/MadGraph5_aMCatNLO:

  python3 make_dim6top_wc_cards_no_reweight.py \
    --template-dir addons/cards/dim6top/ttbbllnunu_dim6top_madspin \
    --outdir addons/cards/dim6top/generated_no_reweight \
    --prefix ttbbllnunu_dim6top \
    --force-rewrite-existing-card-dirs \
    --max-extra-jets 1

Check if all gridpacks are produced:

python3 - <<'PY'
import glob, os, re

wcs = [
    "ctG","ctGI",
    "cQq38","cQq18","cQu8","cQd8",
    "ctq8","ctu8","ctd8",
    "cQq13","cQq11","cQu1","cQd1",
    "ctq1","ctu1","ctd1",
]
pts = ["m4","m2","p0","p2","p4"]

expected = {
    f"ttbbllnunu_dim6top_{wc}_{pt}"
    for wc in wcs for pt in pts
}

found = set()
for f in glob.glob("ttbbllnunu_dim6top_*_slc7_amd64_gcc700_CMSSW_10_6_19_tarball.tar.xz"):
    tag = re.sub(
        r"_slc7_amd64_gcc700_CMSSW_10_6_19_tarball\.tar\.xz$",
        "",
        os.path.basename(f)
    )
    found.add(tag)

missing = sorted(expected - found)
extra = sorted(found - expected)

print("="*60)
print("Expected:", len(expected))
print("Found   :", len(found))
print("Missing :", len(missing))
print("Extra   :", len(extra))
print("="*60)

if missing:
    print("\nMISSING:")
    for x in missing:
        print(x)

if extra:
    print("\nEXTRA:")
    for x in extra:
        print(x)
PY
    

For retry-only workflows, omit --force-rewrite-existing-card-dirs so existing
card directories are left untouched but still included in the command list.
"""
from __future__ import print_function

from pathlib import Path
import argparse
import re
import shutil

WC_LIST = [
    "ctG", "ctGI",
    "cQq38", "cQq18", "cQu8", "cQd8", "ctq8", "ctu8", "ctd8",
    "cQq13", "cQq11", "cQu1", "cQd1", "ctq1", "ctu1", "ctd1",
]
VALUES = [-4, -2, 0, 2, 4]


def shlex_quote(x):
    s = str(x)
    if re.match(r"^[A-Za-z0-9_./:=+${}-]+$", s):
        return s
    return "'" + s.replace("'", "'\"'\"'") + "'"


def tag_value(v):
    return ("p" + str(v)) if v >= 0 else ("m" + str(abs(v)))


def read_template(template_dir, suffix):
    matches = sorted(Path(template_dir).glob("*_{}".format(suffix)))
    if not matches:
        raise IOError("Could not find '*_{}' in {}".format(suffix, template_dir))
    return matches[0].read_text()


def clean_run_card(text):
    """Remove MadSpin/reweight controls and MG5-2.6.5-incompatible options."""
    text = text.replace("_madspin", "")
    lines = []
    for line in text.splitlines():
        low = line.lower()
        if "sde_strategy" in low:
            continue
        if re.search(r"\bmadspin\b", line, re.I):
            continue
        if re.search(r"\breweight\b", line, re.I):
            continue
        lines.append(line)

    lines.append("")
    lines.append("# No-MadSpin fixed-WC debug production")
    return "\n".join(lines).rstrip() + "\n"


def make_proc_card(name, max_extra_jets):
    """Stable-top production only.  No inline decays, no MadSpin."""
    if max_extra_jets < 0 or max_extra_jets > 3:
        raise ValueError("--max-extra-jets must be 0, 1, 2, or 3")

    lines = [
        "import model dim6top_LO_UFO",
        "",
        "set group_subprocesses Auto",
        "set ignore_six_quark_processes False",
        "set loop_optimized_output True",
        "set low_mem_multicore_nlo_generation False",
        "set loop_color_flows False",
        "set gauge unitary",
        "set complex_mass_scheme False",
        "set max_npoint_for_channel 0",
        "",
        "define p = g u c d s u~ c~ d~ s~ b b~",
        "define j = g u c d s u~ c~ d~ s~ b b~",
        "define l+ = e+ mu+ ta+",
        "define l- = e- mu- ta-",
        "define vl = ve vm vt",
        "define vl~ = ve~ vm~ vt~",
        "",
        "generate p p > t t~ FCNC=0 DIM6=1 @0",
    ]
    for njet in range(1, max_extra_jets + 1):
        jets = " ".join(["j"] * njet)
        lines.append("add process p p > t t~ {} FCNC=0 DIM6=1 @{}".format(jets, njet))
    lines += ["", "output {} -nojpeg".format(name), ""]
    return "\n".join(lines)


def make_customize_card(text, wc, value):
    text = text.replace("_madspin", "")
    out = []
    seen = set()
    number = r"[-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?|[-+]?\.\d+(?:[eE][-+]?\d+)?"
    wc_line_re = re.compile(r"^(\s*set\s+param_card\s+)(\S+)(\s+)({})(.*)$".format(number))
    for line in text.splitlines():
        m = wc_line_re.match(line)
        if m and m.group(2) in WC_LIST:
            par = m.group(2)
            seen.add(par)
            val = value if par == wc else 0
            out.append("{}{}{}{:g}{}".format(m.group(1), par, m.group(3), val, m.group(5)))
        else:
            out.append(line)
    for par in WC_LIST:
        if par not in seen:
            val = value if par == wc else 0
            out.append("set param_card {} {:g}".format(par, val))
    return "\n".join(out).rstrip() + "\n"


def write_run_script(commands_path, made, outdir, gridpack_script, queue, jobstep, scram_arch, cmssw_version):
    lines = [
        "#!/usr/bin/env bash",
        "",
        "# Auto-generated by make_dim6top_wc_cards_no_reweight_parallel.py",
        "# One standalone gridpack command per line.",
        "# Environment setup belongs inside each SLURM job, not here.",
        "",
    ]
    for name in made:
        card_path = str(outdir / name)
        cmd = [
            "./{}".format(gridpack_script.lstrip("./")),
            shlex_quote(name),
            shlex_quote(card_path),
            shlex_quote(queue),
            shlex_quote(jobstep),
            shlex_quote(scram_arch),
            shlex_quote(cmssw_version),
        ]
        lines.append(" ".join(cmd))
    lines.append("")
    commands_path.write_text("\n".join(lines))
    commands_path.chmod(commands_path.stat().st_mode | 0o111)


def write_cards(card_dir, name, run_template, customize_template, wc, value, max_extra_jets):
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / "{}_customizecards.dat".format(name)).write_text(make_customize_card(customize_template, wc, value))
    (card_dir / "{}_proc_card.dat".format(name)).write_text(make_proc_card(name, max_extra_jets))
    (card_dir / "{}_run_card.dat".format(name)).write_text(clean_run_card(run_template))
    for bad in card_dir.glob("*madspin*"):
        if bad.is_file():
            bad.unlink()
    for bad in card_dir.glob("*reweight*"):
        if bad.is_file():
            bad.unlink()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template-dir", required=True, type=Path,
                    help="Directory containing the original template cards; may include _madspin in input name")
    ap.add_argument("--outdir", required=True, type=Path,
                    help="Output directory where generated card directories will be written")
    ap.add_argument("--prefix", default="ttbbllnunu_dim6top",
                    help="Prefix for generated card directory/file names; should not contain _madspin")
    ap.add_argument("--overwrite", action="store_true",
                    help="Alias for --force-rewrite-existing-card-dirs")
    ap.add_argument("--force-rewrite-existing-card-dirs", action="store_true",
                    help="Rewrite existing generated card dirs. Default: leave them untouched.")
    ap.add_argument("--gridpack-script", default="gridpack_generation_dim6top.sh")
    ap.add_argument("--queue", default="local")
    ap.add_argument("--jobstep", default="ALL")
    ap.add_argument("--scram-arch", default="slc7_amd64_gcc700")
    ap.add_argument("--cmssw-version", default="CMSSW_10_6_19")
    ap.add_argument("--commands-file", default="run_all_gridpacks.sh")
    ap.add_argument("--max-extra-jets", type=int, default=1,
                    help="0 for inclusive ttbar only, 1 for 0/1-jet MLM-style production, up to 3")
    args = ap.parse_args()

    if "madspin" in args.prefix.lower():
        raise ValueError("Refusing generated prefix containing 'madspin': {}".format(args.prefix))

    run_template = read_template(args.template_dir, "run_card.dat")
    customize_template = read_template(args.template_dir, "customizecards.dat")
    args.outdir.mkdir(parents=True, exist_ok=True)

    rewrite = args.overwrite or args.force_rewrite_existing_card_dirs
    made = []
    for wc in WC_LIST:
        for value in VALUES:
            name = "{}_{}_{}".format(args.prefix, wc, tag_value(value))
            d = args.outdir / name
            if d.exists() and rewrite:
                shutil.rmtree(str(d))
                write_cards(d, name, run_template, customize_template, wc, value, args.max_extra_jets)
            elif d.exists():
                print("[SKIP existing card dir] {}".format(d))
            else:
                write_cards(d, name, run_template, customize_template, wc, value, args.max_extra_jets)
            made.append(name)

    commands_path = args.outdir / args.commands_file
    write_run_script(commands_path, made, args.outdir, args.gridpack_script, args.queue,
                     args.jobstep, args.scram_arch, args.cmssw_version)

    print("[OK] Command list covers {} card directories under {}".format(len(made), args.outdir))
    print("[OK] Wrote BSMRef-style command file: {}".format(commands_path))
    print("[OK] No MadSpin cards are written; proc cards are stable-top production only.")


if __name__ == "__main__":
    main()
