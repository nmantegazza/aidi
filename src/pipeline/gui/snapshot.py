import pickle
import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = Path("outputs/snapshots")

def get_snapshot_dir() -> Path:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    return SNAPSHOT_DIR

def save_snapshot(name: str, state_dict: Dict[str, Any]) -> Path:
    """Serializes the state dictionary to a pickle file."""
    if not name.endswith(".pkl"):
        name += ".pkl"
    
    # Sanitize name
    name = Path(name).name
    
    target_path = get_snapshot_dir() / name
    
    logger.info(f"Saving snapshot to {target_path}")
    with open(target_path, "wb") as f:
        pickle.dump(state_dict, f)
        
    return target_path

def load_snapshot(name: str) -> Dict[str, Any]:
    """Deserializes the state dictionary from a pickle file."""
    if not name.endswith(".pkl"):
        name += ".pkl"
        
    name = Path(name).name
    target_path = get_snapshot_dir() / name
    
    if not target_path.exists():
        raise FileNotFoundError(f"Snapshot file not found: {target_path}")
        
    logger.info(f"Loading snapshot from {target_path}")
    with open(target_path, "rb") as f:
        state_dict = pickle.load(f)
        
    return state_dict

def list_snapshots() -> List[str]:
    """Lists all available snapshot filenames (without path)."""
    directory = get_snapshot_dir()
    return sorted([f.name for f in directory.glob("*.pkl")])
