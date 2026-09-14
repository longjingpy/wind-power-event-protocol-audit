"""Build the editorial preparation package from existing evidence; no experiments.

Uses the downloaded Elsevier class and numeric bibliography style. The source
bundle is flat because the publisher's Editorial Manager guidance requires it.
"""
from pathlib import Path
import csv
import json
import re
import os
import shutil
import subprocess
import zipfile

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "manuscript/applied_energy"
BUILD = ROOT / "temp/applied_energy_build"
SOURCES = OUT / "submission_source"
DATA_OUT = Path(os.environ.get("WPF_EVIDENCE_OUT", str(ROOT / "outputs/dynamic_events_v6")))
DOWN_OUT = ROOT / "outputs/downstream_v6"


def latex(text):
    text = re.sub(r"^(#+)\s+\d+(?:\.\d+)*\.\s+", r"\1 ", text, flags=re.M)
    return subprocess.run(
        ["pandoc", "-f", "markdown+tex_math_single_backslash", "-t", "latex", "--natbib", "--no-highlight", "--wrap=none"],
        input=text, text=True, capture_output=True, check=True,
    ).stdout.strip()


def read_rows(name):
    with (DATA_OUT / name).open(newline="") as f:
        return list(csv.DictReader(f))


def table(title, headers, rows):
    escape = lambda x: str(x).replace("|", "/").replace("\n", " ")
    return "\n\n### " + title + "\n\n" + "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + "\n".join("| " + " | ".join(escape(v) for v in row) + " |" for row in rows) + "\n"


def supplement_tables():
    text = "\n\n## Supplementary result tables\n\nThe tables present the evaluation populations and measures defined in Supplementary Methods S1–S10. Calendar-block intervals summarize temporal variation within each farm. Seed and batch summaries describe their stated computational units.\n"
    def detector_name(value):
        return (value.replace("endpoint_corridor", "Corridor")
                     .replace("adaptive_corridor", "Adaptive corridor")
                     .replace("financial_tail", "Tail")
                     .replace("mean_shift", "Mean shift")
                     .replace("threshold", "Threshold")
                     .replace("opsda_cui2015", "OpSDA")
                     .replace("sda_florita2013", "SDA")
                     .replace("_", " "))
    f3 = lambda v: f"{float(v):.3f}"
    names = {"hill": "Hill of Towie", "lahaute": "La Haute Borne", "pizhou": "Pizhou", "suining": "Suining", "yandun": "Yandun", "greece": "Greece"}
    rows = read_rows("representation_summary_primary.csv")
    text += table("Table S1. Primary representation comparison (k = 4)", ["Site/group", "Representation", "NMI", "ARI", "Agreement"], [[names.get(r["group"], r["group"]), r["representation"].replace("_", " "), f3(r["nmi"]), f3(r["ari"]), f3(r["agreement"])] for r in rows])
    rows = read_rows("block_intervals.csv")
    text += table("Table S2. Raw25 block-length sensitivity", ["Site/group", "Days", "Occupied blocks", "Paired records", "NMI [95% interval]"], [[names.get(r["group"], r["group"]), r["block_days"], r["occupied_blocks"], r["pairs"], f'{f3(r["nmi"])} [{f3(r["nmi_low"])}, {f3(r["nmi_high"])}]'] for r in rows if r["representation"] == "raw25"])
    rows = read_rows("external_greece/summary_by_sample_size.csv")
    text += table("Table S3. Greek configuration-pair support strata", ["Matches per pair", "Configuration pairs", "Median NMI", "Minimum", "Maximum"], [[r["sample_bin"], r["configuration_pairs"], f3(r["median_nmi"]), f3(r["min_nmi"]), f3(r["max_nmi"])] for r in rows])
    rows = read_rows("weather_mechanism/risk_by_horizon.csv") + read_rows("weather_mechanism/noaa_ground_proxy_risk.csv")
    text += table("Table S4. Descriptive weather contrasts", ["Source", "Horizon (h)", "Exposed n", "Control n", "Risk exposed", "Risk control", "Difference"], [["NOAA proxy" if r["exposure"].startswith("noaa") else "ERA5", r["horizon_h"], r["treated_n"], r["control_n"], f3(r["treated_risk"]), f3(r["control_risk"]), f3(r["risk_difference"])] for r in rows])
    rows = read_rows("weather_mechanism/time_shift_placebo.csv")
    text += table("Table S5. Archived time-displacement diagnostics (4 h outcome)", ["Displacement", "Exposed n", "Control n", "Risk difference"], [[r["exposure"].replace("_treatment", ""), r["treated_n"], r["control_n"], f3(r["risk_difference"])] for r in rows])
    rows = read_rows("weather_mechanism/mechanism_chain_recovery_effects.csv")
    text += table("Table S6. Scaled post-event power index and residual-power contrasts", ["Measure", "Events", "Exposed minus control", "95% block interval"], [[{"recovery_fraction_4h": "Scaled post-event power index", "residual_4h": "Residual power", "response_abs": "Absolute power response"}.get(r["metric"], r["metric"].replace("_", " ")), r["n"], f3(r["difference_exposed_minus_unexposed"]), f'[{f3(r["ci95_low"])}, {f3(r["ci95_high"])}]'] for r in rows])
    decision = ROOT / "outputs/real_decision_v9_signed"
    if (decision / "forecast_summary.csv").exists():
        rows = list(csv.DictReader((decision / "forecast_summary.csv").open(newline="")))
        text += table("Table S7. Forecasts on common chronological targets", ["Site", "Model", "Training", "Subset", "n", "nMAE (%)"], [[r["site"], r["model"], r["training"].replace("_", " "), r["subset"].replace("_", " "), r["n"], f3(r["nmae"])] for r in rows])
    if (decision / "economic_summary.csv").exists():
        rows = list(csv.DictReader((decision / "economic_summary.csv").open(newline="")))
        text += table("Table S8. Validation-selected storage scenario costs", ["Site", "Model", "Training", "Scenario", "P (MW/MW)", "E (MWh/MW)", "Cost (CNY per norm. MW)"], [[r["site"], r["model"], r["training"].replace("_", " "), r["scenario"], f3(r["power"]), f3(r["energy"]), f3(r["cost"])] for r in rows])
    controlled = ROOT / "outputs/detection_benchmark_v9/protocol_ablation_metrics.csv"
    if controlled.exists():
        rows = list(csv.DictReader(controlled.open(newline="")))
        rows = [r for r in rows if r["split"] == "test"]
        text += table("Table S9. Controlled synthetic event detection (IoU >= 0.3)", ["Model", "Seed", "Policy", "Precision", "Recall", "F1"], [[r["model"], r["seed"], r["policy"].replace("_", " "), f3(r["precision"]), f3(r["recall"]), f3(r["f1"])] for r in rows])
    annotation = ROOT / "outputs/annotation_v9/sampling_support.csv"
    if annotation.exists():
        rows = list(csv.DictReader(annotation.open(newline="")))
        text += table("Table S10. Human-review sampling support", ["Site", "Sampling stratum", "Windows"], [[r["site"], r["stratum"].replace("_", " "), r["actual"]] for r in rows])
    human_metrics = ROOT / "outputs/user_labels_v9/window_detector_metrics.csv"
    if human_metrics.exists():
        rows = list(csv.DictReader(human_metrics.open(newline="")))
        text += table("Table S11. Human-labelled centre-region detector agreement", ["Site", "Detector", "Windows", "TP", "FP", "FN", "Precision", "Recall", "F1"], [[r["site"], detector_name(r["config"]), r["n_windows"], r["tp"], r["fp"], r["fn"], f3(r["precision"]), f3(r["recall"]), f3(r["f1"])] for r in rows])
    learned = pd.read_csv(ROOT / "outputs/cv_benchmark_v7_100_complete/cv_benchmark_metrics.csv")
    farm_groups = ["pairs:" + name for name in ["pizhou", "suining", "yandun", "lahaute", "hill"]]
    learned = learned[(learned.k == 4) & learned.group.isin(farm_groups)]
    text += table("Table S12. Learned representations by farm, averaged over three seeds (k = 4)",
                  ["Representation", "Farm", "NMI", "ARI"],
                  [[rep.replace("_", " "), names.get(group.replace("pairs:", ""), group),
                    f3(part.nmi.mean()), f3(part.ari.mean())]
                   for (rep, group), part in learned.groupby(["representation", "group"])])
    weighted = pd.read_csv(ROOT / "outputs/matching_coverage_v12/coverage_weighted_agreement.csv")
    iou = pd.read_csv(ROOT / "outputs/matching_coverage_v12/iou_threshold_sensitivity.csv")
    pair = pd.read_csv(ROOT / "outputs/matching_coverage_v12/pair_coverage_summary.csv")
    comp_rows = [[names.get(r["group"], r["group"]), f3(r["pair_weighted_nmi"]), f3(r["pair_weighted_ari"]), str(int(r["total_pairs"])),
                  f3(pair[pair.site == r["group"]].left_coverage.mean()), f3(pair[pair.site == r["group"]].right_coverage.mean()),
                  f3(iou[iou.site == r["group"]].fraction_iou_ge_030.iloc[0]),
                  f3(iou[iou.site == r["group"]].fraction_iou_ge_050.iloc[0]),
                  f3(iou[iou.site == r["group"]].fraction_iou_ge_070.iloc[0])]
                 for _, r in weighted.iterrows()]
    text += table("Table S14. Matched-count-weighted agreement and detector-occupancy overlap",
                  ["Site", "Weighted NMI", "Weighted ARI", "Pairs", "Left cov.", "Right cov.", "IoU >= 0.3", "IoU >= 0.5", "IoU >= 0.7"], comp_rows)
    external = pd.read_csv(ROOT / "outputs/sdwpf_v7/learned_forward_metrics.csv")
    text += table("Table S13. SDWPF learned-model transfer across seven batches and three seeds",
                  ["Representation", "k", "Runs", "Mean NMI", "SD NMI", "Mean ARI"],
                  [[rep, k, len(part), f3(part.nmi.mean()), f3(part.nmi.std()), f3(part.ari.mean())]
                   for (rep, k), part in external.groupby(["representation", "k"])])
    weather = pd.read_csv(ROOT / "outputs/weather_uncertainty_v12/risk_block_intervals.csv")
    text += table("Table S15. Observational weather contrasts with shared calendar-block intervals",
                  ["Source", "Horizon (h)", "Block days", "Blocks", "Risk difference", "95% interval"],
                  [[r.source, r.horizon_h, r.block_days, r.occupied_blocks, f3(r.risk_difference),
                    f"[{f3(r.ci95_low)}, {f3(r.ci95_high)}]"] for r in weather.itertuples()])
    return text


PREAMBLE = r"""\documentclass[preprint,12pt]{elsarticle}
\usepackage[a4paper,left=22mm,right=22mm,top=22mm,bottom=22mm]{geometry}
\usepackage{fontspec}
\setmainfont{TeX Gyre Termes}
\setsansfont{TeX Gyre Heros}
\usepackage{amsmath,amssymb,booktabs,longtable,array,calc,graphicx}
\usepackage{caption,float}
\usepackage{needspace}
\usepackage{xurl}
\usepackage{fvextra}
\DefineVerbatimEnvironment{verbatim}{Verbatim}{breaklines=true,fontsize=\footnotesize}
\usepackage[colorlinks=true,allcolors=black,breaklinks=true]{hyperref}
\usepackage{lineno}
\modulolinenumbers[5]
\biboptions{sort&compress}
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\providecommand{\passthrough}[1]{#1}
\setlength{\emergencystretch}{3em}
\sloppy
\journal{Applied Energy}
\begin{document}
"""


def compile_tex(name):
    subprocess.run(["latexmk", "-xelatex", "-interaction=nonstopmode", "-halt-on-error", "-file-line-error", f"-outdir={BUILD}", name + ".tex"], cwd=SOURCES, check=True, stdout=(BUILD / f"{name}_build_stdout.txt").open("w"), stderr=subprocess.STDOUT)
    shutil.copy2(BUILD / f"{name}.pdf", OUT / f"{name}.pdf")
    bbl = BUILD / f"{name}.bbl"
    if bbl.exists():
        shutil.copy2(bbl, SOURCES / bbl.name)


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    SOURCES.mkdir(parents=True, exist_ok=True)
    meta = json.loads((OUT / "frontmatter.json").read_text())
    assert 3 <= len(meta["highlights"]) <= 5
    assert all(len(s) <= 85 for s in meta["highlights"])
    bundle = OUT / "official_template/elsarticle/elsarticle"
    for name in ["elsarticle.cls", "elsarticle-num.bst"]:
        shutil.copy2(bundle / name, SOURCES / name)
    shutil.copy2(OUT / "references.bib", SOURCES / "references.bib")
    for i in range(1, 9):
        shutil.copy2(OUT / f"figures/fig{i}.pdf", SOURCES / f"fig{i}.pdf")
    caption_text = (OUT / "figure_captions.md").read_text()
    captions = re.findall(r"^Fig\. (\d+)\. (.*?)(?=\n\nFig\.|\Z)", caption_text, flags=re.M | re.S)
    assert len(captions) == 8
    body = latex((OUT / "manuscript_body.md").read_text())
    # Place each figure beside the result it explains.
    cap_map = {number: caption.strip() for number, caption in captions}
    def inline_fig(number, anchor):
        figure = (r"\setcounter{figure}{" + str(int(number)-1) + "}\n" + r"\begin{figure}[H]\centering" + "\n" +
                  r"\includegraphics[width=0.92\linewidth]{fig" + number + ".pdf}\n" +
                  r"\caption{" + latex(cap_map[number]) + "}\n" +
                  r"\label{fig:" + number + "}" + "\n" + r"\end{figure}" + "\n")
        nonlocal body
        if anchor not in body:
            raise RuntimeError("inline anchor missing: " + anchor)
        body = body.replace(anchor, anchor + "\n\n" + figure, 1)
    inline_fig("1", "The framework supports a compact reporting record for future ramp studies and gives flexibility analyses a traceable measurement layer.")
    inline_fig("2", "Together, support and coverage give the reader both the amount of comparative evidence and its reach within the catalogue (Figs. 1 and 2).")
    inline_fig("3", "Figure 3 displays the fixed-feature comparison.")
    inline_fig("4", "These comparisons describe sensitivity to grouping resolution (Fig. 4).")
    inline_fig("5", "The NMI describes retained shape grouping, and the coverage identifies the fraction of candidate support reached by temporal matching (Fig. 5).")
    inline_fig("6", "Each comparison describes its own observation coverage and atmospheric measurement scale.")
    inline_fig("7", "Figure 7 places these external estimates beside the primary learned-model comparison.")
    inline_fig("8", "A local mean-change rule reaches F1 0.741 on this generator.")
    body = body.replace("Table 1. Primary SCADA population and half-hour input eligibility.", "\\needspace{8\\baselineskip}\\textbf{Table 1.} Primary SCADA population and half-hour input eligibility.")
    body = body.replace(r"\begin{longtable}", r"\begingroup\small\setlength{\tabcolsep}{3pt}" + "\n" + r"\begin{longtable}")
    body = body.replace(r"\end{longtable}", r"\end{longtable}" + "\n" + r"\endgroup")
    body = re.sub(r"(?m)^Table (\d+)\. (.+)$",
                  lambda match: r"\needspace{9\baselineskip}\textbf{Table " + match[1] + ".} " + match[2], body)
    (SOURCES / "body.tex").write_text(body)
    author_lines = []
    for a in meta["authors"]:
        mark = a["superscripts"]
        corr = r"\corref{cor1}" if a.get("corresponding") else ""
        email = r"\ead{" + a["email"] + "}"
        orcid = r"\textsuperscript{ORCID: " + a["orcid"] + "}"
        author_lines.append(r"\author[aff" + mark.replace(",", ",aff") + "]{" + a["name"] + corr + " " + orcid + "}" + email)
    affiliation_lines = []
    for i, aff in enumerate(meta["affiliations"], start=1):
        affiliation_lines.append(r"\address[aff" + str(i) + "]{" + aff + "}")
    front = r"\begin{frontmatter}" + "\n" + r"\title{" + latex(meta["title"]) + r"}" + "\n" + "\n".join(author_lines + affiliation_lines) + "\n" + r"\cortext[cor1]{Correspondence: Chaoxia Yuan, chaoxia.yuan@nuist.edu.cn}" + "\n" + r"\begin{abstract}" + "\n" + latex(meta["abstract"]) + "\n" + r"\end{abstract}" + "\n" + r"\begin{keyword}" + "\n" + " \\sep ".join(latex(k) for k in meta["keywords"]) + "\n" + r"\end{keyword}\end{frontmatter}" + "\n"
    declarations = "\n"
    for heading, key in [
        ("Data availability", "data_availability"),
        ("Funding", "funding"),
        ("Author contributions", "author_contributions"),
        ("Acknowledgements", "acknowledgements"),
        ("Competing interests", "conflicts"),
    ]:
        declarations += "\\section*{" + heading + "}\n" + latex(meta[key]) + "\n"
    main_tex = PREAMBLE + front + "\\linenumbers\n\\input{body}\n" + declarations + "\n\\nolinenumbers\\bibliographystyle{elsarticle-num}\\bibliography{references}\n\\end{document}\n"
    (SOURCES / "main.tex").write_text(main_tex)
    supp_md = (OUT / "supplementary_methods.md").read_text() + supplement_tables()
    (OUT / "supplementary_complete.md").write_text(supp_md)
    supp_latex = latex(supp_md)
    for heading in ["section", "subsection", "subsubsection"]:
        supp_latex = supp_latex.replace("\\" + heading + "{", "\\" + heading + "*{")
    # Give the detector field enough room while preserving readable numeric columns.
    start = supp_latex.index("Table S11.")
    end = supp_latex.index("Table S12.", start)
    fragment = supp_latex[start:end]
    widths = iter([0.12, 0.24, 0.10, 0.06, 0.06, 0.06, 0.12, 0.12, 0.12])
    fragment = re.sub(r"\\real\{0\.1111\}", lambda _: r"\real{" + f"{next(widths):.4f}" + "}", fragment)
    supp_latex = supp_latex[:start] + fragment + supp_latex[end:]
    supp_tex = PREAMBLE + r"\begin{frontmatter}\title{Supplementary material: " + latex(meta["title"]) + r"}\begin{abstract}Methods and result tables for the seven-archive study, including learned representations, external transfer, human-reviewed regions, controlled episode localization and chronological forecasting.\end{abstract}\end{frontmatter}" + "\n\\small\\setlength{\\tabcolsep}{3pt}\n" + supp_latex + "\n\\clearpage\n\\bibliographystyle{elsarticle-num}\\bibliography{references}\n\\end{document}\n"
    (SOURCES / "supplementary.tex").write_text(supp_tex)
    compile_tex("main")
    compile_tex("supplementary")
    with zipfile.ZipFile(OUT / "latex_source_flat.zip", "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in sorted(SOURCES.iterdir()):
            if file.is_file():
                archive.write(file, arcname=file.name)
    checks = {"abstract_words": len(meta["abstract"].split()), "highlight_characters": [len(s) for s in meta["highlights"]], "source_files_flat": True, "evidence_refit": False}
    (BUILD / "build_checks.json").write_text(json.dumps(checks, indent=2))
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
