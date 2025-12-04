"""Generate JSON format gap analysis report."""
import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_json_report(
    gaps: Dict[str, Any],
    summary: Dict[str, Any],
    action_plan: list[Dict[str, Any]],
    quick_wins: list[Dict[str, Any]],
    config: Dict[str, Any],
    output_path: str = "reports/gap_report.json"
) -> None:
    """
    Generate comprehensive JSON report.
    
    Args:
        gaps: All detected gaps
        summary: Executive summary
        action_plan: Prioritized action plan
        quick_wins: Quick win opportunities
        config: Configuration used
        output_path: Output file path
    """
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'primary_site': config.get('site', 'Unknown'),
            'competitors_analyzed': len(config.get('competitors', [])),
            'version': '1.0'
        },
        'summary': summary,
        'gaps': gaps,
        'action_plan': action_plan,
        'quick_wins': quick_wins,
        'config': {
            'similarity_threshold': config.get('similarity_threshold', 0.45),
            'chunk_size': config.get('chunk_size', 1500),
            'thin_content_ratio': config.get('thin_content_ratio', 3.0)
        }
    }
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    logger.info(f"JSON report saved to {output_path}")


def save_detailed_gaps(
    gaps_with_analysis: list[Dict[str, Any]],
    output_path: str = "reports/detailed_gaps.json"
) -> None:
    """
    Save detailed gap analysis including LLM comparisons.
    
    Args:
        gaps_with_analysis: Gaps with LLM analysis
        output_path: Output file path
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(gaps_with_analysis, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Detailed gaps saved to {output_path}")
