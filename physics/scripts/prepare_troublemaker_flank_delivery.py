"""Stage the verified flank revision and retain its current playable parent."""
from pathlib import Path
from audit_troublemaker_inferred_flanks import main as geometry_audit, ROOT
from prepare_troublemaker_sparse_rock_delivery import stage_delivery


def main():
    reviews = ROOT/'docs/reconstruction-review-2026-09-06'
    stage_delivery(*geometry_audit(),
        ROOT/'tmp/south-fork-survey-hydraulics/1m-mixed-inlet-inferred-rock-flanks-20260912',
        ROOT/'tmp/troublemaker-playable-before-inferred-flanks-20260912',
        reviews/'troublemaker_survey_flow_1m-mixed-inlet-inferred-rock-flanks-20260912.json',
        reviews/'troublemaker_numerical_boundary_flux-inferred-rock-flanks-20260912.json')


if __name__ == '__main__':
    main()
