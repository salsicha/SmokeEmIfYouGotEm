"""Field-only candidate update using the existing fail-closed staging checks."""
import importlib.util
import json
from pathlib import Path

SCRIPT=Path(__file__).with_name('stage_south_fork_triangle_review.py')
spec=importlib.util.spec_from_file_location('survey_triangle_staging',SCRIPT)
stage=importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage)
stage.BEFORE_SHA='a54447bbc029acfe40dfed0cd3379e8119dab1cc49d304ead558d37b558ae7cb'
stage.OLD_FIELDS=stage.NEW_FIELDS
stage.NEW_FIELDS='tmp/south-fork-survey-hydraulics/1m-mixed-inlet-depth-limited-hydrostatic-20260907/engine_review'
stage.BACKUP=Path('tmp/project-cleanup/SouthForkSurveyPlayable-before-depth-limited-fields.umap')
stage.REPORT=Path('docs/reconstruction-review-2026-09-07/depth-limited-engine-integration.json')


def main():
    if stage.sha(stage.ROOT/'physics/cpp/build-ue/raftsim_water.lib')!='83f35ddf4e6ab28fc07999804e63d3ccfcd5d0d78d8f0775c96e909913910f03':
        raise ValueError('Engine-linked archive does not match this candidate build')
    fields=json.loads((stage.ROOT/stage.NEW_FIELDS/'manifest.json').read_text())
    if fields['review'].get('source_solver_binary_sha256')!='1f010cbe7edce8eb579c2d9a040820a24d6ee6ac1615073e3afbf899cac9ba50':
        raise ValueError('Wrong candidate numerical core')
    stage.main()


if __name__=='__main__':
    import unreal
    try:main()
    finally:unreal.SystemLibrary.quit_editor()
