from typing import Dict, Any, NamedTuple, Callable

from .phases.phase_1_ingestion import build_phase_1
from .phases.phase_2_cleaning import build_phase_2
from .phases.phase_3_matching import build_phase_3
from .phases.phase_4_porting import build_phase_4
from .phases.phase_5_linkage import build_phase_5
from .phases.phase_6_results import build_phase_6

from .handlers import (
    handle_ingestion,
    handle_cleaning,
    handle_schema_matching,
    handle_data_porting,
    handle_record_linkage,
    handle_results
)

class PhaseInfo(NamedTuple):
    index: int
    label: str
    build_fn: Callable
    handler_fn: Callable

PHASE_REGISTRY: Dict[int, PhaseInfo] = {
    0: PhaseInfo(0, "1. Ingestion", build_phase_1, handle_ingestion),
    1: PhaseInfo(1, "2. Cleaning", build_phase_2, handle_cleaning),
    2: PhaseInfo(2, "3. Schema Matching", build_phase_3, handle_schema_matching),
    3: PhaseInfo(3, "4. Data Porting", build_phase_4, handle_data_porting),
    4: PhaseInfo(4, "5. Record Linkage", build_phase_5, handle_record_linkage),
    5: PhaseInfo(5, "6. Results", build_phase_6, handle_results)
}
