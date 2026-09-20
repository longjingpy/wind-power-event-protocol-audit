"""Assemble a flat source packet and explicit public v23 additions.

Existing research history is preserved. Only authored code, aggregate result
tables and manuscript assets enter the public tree; internal event clocks and
individual annotation exports are not copied by this command.
"""
from pathlib import Path
import json
import re
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'manuscript/applied_energy'
DEST = DOC / 'submission_v23'
PUBLIC = ROOT / 'public_release'


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ['main.pdf', 'supplementary.pdf', 'manuscript_body.md',
                 'supplementary_methods.md', 'supplementary_complete.md', 'frontmatter.json']:
        copy(DOC / name, DEST / name)
        copy(DOC / name, PUBLIC / 'manuscript/applied_energy' / name)
    for build, tex in [('v19_manuscript_build', 'main.tex'), ('v19_supplementary_build', 'supplementary.tex')]:
        source = ROOT / 'temp' / build
        copy(source / tex, DEST / tex)
        copy(source / tex, PUBLIC / 'manuscript/applied_energy' / tex)
        for image in re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', (source / tex).read_text(encoding='utf-8')):
            copy(source / image, DEST / image)
            copy(source / image, PUBLIC / 'manuscript/applied_energy' / image)
        for name in ['references.bib', 'elsarticle.cls', 'elsarticle-num.bst']:
            if (source / name).exists():
                copy(source / name, DEST / name)
                copy(source / name, PUBLIC / 'manuscript/applied_energy' / name)
    for dirname in ['figures_v22', 'figures_v23']:
        for source in (ROOT / 'manuscript' / dirname).iterdir():
            if source.is_file() and source.suffix in ['.pdf', '.svg', '.png', '.csv', '.drawio', '.md']:
                copy(source, PUBLIC / 'manuscript' / dirname / source.name)
                copy(source, DEST / dirname / source.name)
    copy(ROOT / 'manuscript/figures_v22/fig01_workflow.drawio', DEST / 'fig01_workflow.drawio')
    for directory in [ROOT / 'outputs/protocol_benchmark_v23', ROOT / 'outputs/protocol_benchmark_v22/economics']:
        for source in directory.rglob('*'):
            if source.is_file() and source.suffix in ['.csv', '.json']:
                relative = source.relative_to(ROOT / 'outputs')
                copy(source, PUBLIC / 'results' / relative)
                copy(source, DEST / 'result_tables' / relative)
    for source in (ROOT / 'src/wind_events').glob('*.py'):
        copy(source, PUBLIC / 'src/wind_events' / source.name)
    for name in ['many_to_many_v23.py', 'cluster_sensitivity_v23.py', 'reconcile_coverage_v23.py',
                 'integrate_overlap_v23.py', 'finalize_text_v23.py', 'package_current_v23.py',
                 'verify_manuscript_v23.py', 'create_fig01_drawio.py', 'export_drawio_v23.py',
                 'redraw_manuscript_v22.py', 'storage_capability_v22.py',
                 'conditional_structure_v18.py', 'run_structure_v18.py', 'literature_detectors_v5.py',
                 'build_v18_manuscript.py', 'build_supplementary_v18.py', 'assemble_figure_selection_v22.py']:
        copy(ROOT / 'script' / name, PUBLIC / 'script' / name)
    for name in ['test_overlap_graph_v23.py', 'test_protocol_v18.py', 'test_representation_v18.py',
                 'test_economics_v18.py', 'test_conditional_v18.py']:
        copy(ROOT / 'tests' / name, PUBLIC / 'tests' / name)
    for name in ['V23_REVIEW_RESPONSE.md']:
        copy(ROOT / 'docs' / name, PUBLIC / 'docs' / name)
        copy(ROOT / 'docs' / name, DEST / name)
    readme = '''# Current manuscript source packet (v23)

The canonical manuscript is main.pdf, with the complete supplementary.pdf.
The two TeX files and their referenced figures are flat in this directory.
Compile with XeLaTeX, BibTeX, then XeLaTeX twice; the checked toolchain is TeX
Live 2026. The editable workflow is fig01_workflow.drawio. Figure source/data
folders retain PDF, SVG, PNG and table variants for author editing.

This packet updates the manuscript, supplement, experimental tables and figure
assets. Author declarations, submission metadata and the cover letter require
the authors' final journal-submission check. No journal upload was performed.

See V23_REVIEW_RESPONSE.md for the six requested clarifications, two independent
review rounds and completed overlap experiments. Public release v0.5.0 links
the earlier de-identified SCADA distribution; raw provider licences persist.
'''
    (DEST / 'README_SUBMISSION.md').write_text(readme, encoding='utf-8')
    files = sorted(p for p in DEST.rglob('*') if p.is_file())
    with zipfile.ZipFile(DOC / 'AppliedEnergy_current_v23.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for source in files:
            archive.write(source, source.relative_to(DEST))
    report = {'status': 'ASSEMBLED', 'files': len(files), 'main_figures': 14,
              'internal_clock_ledger_published': False, 'individual_rater_exports_copied': False,
              'source_package': 'AppliedEnergy_current_v23.zip'}
    (ROOT / 'temp/v23_package_report.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
