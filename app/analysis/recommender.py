"""Generate recommendations based on gap analysis."""
from typing import Any, Dict, List

from app.utils.logger import get_logger

logger = get_logger(__name__)


def prioritize_gaps(gaps: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Prioritize all gaps by impact and urgency.
    
    Args:
        gaps: Dictionary of all gap types
        
    Returns:
        Sorted list of prioritized gaps
    """
    all_gaps = []
    
    # Add priority scores
    priority_weights = {
        'high': 3,
        'medium': 2,
        'low': 1
    }
    
    # Process missing pages
    for gap in gaps.get('missing_pages', []):
        gap['category'] = 'Missing Content'
        gap['impact_score'] = priority_weights.get(gap.get('priority', 'medium'), 2)
        # Lower similarity = higher impact
        gap['impact_score'] += (1 - gap.get('similarity_score', 0.5)) * 2
        all_gaps.append(gap)
    
    # Process thin content
    for gap in gaps.get('thin_content', []):
        gap['category'] = 'Thin Content'
        gap['impact_score'] = priority_weights.get(gap.get('priority', 'medium'), 2)
        # Higher ratio = higher impact
        gap['impact_score'] += min(gap.get('ratio', 3.0) / 3.0, 2)
        all_gaps.append(gap)
    
    # Process metadata gaps
    for gap in gaps.get('metadata_gaps', []):
        gap['category'] = 'Metadata Issues'
        gap['impact_score'] = priority_weights.get(gap.get('priority', 'medium'), 2)
        # More missing elements = higher impact
        gap['impact_score'] += len(gap.get('missing_elements', []))
        all_gaps.append(gap)
    
    # Process schema gaps
    for gap in gaps.get('schema_gaps', []):
        gap['category'] = 'Schema Missing'
        gap['impact_score'] = priority_weights.get(gap.get('priority', 'medium'), 2)
        all_gaps.append(gap)
    
    # Sort by impact score
    all_gaps.sort(key=lambda x: x.get('impact_score', 0), reverse=True)
    
    logger.info(f"Prioritized {len(all_gaps)} total gaps")
    return all_gaps


def generate_action_plan(prioritized_gaps: List[Dict[str, Any]], max_items: int = 20) -> List[Dict[str, Any]]:
    """
    Generate actionable plan from prioritized gaps.
    
    Args:
        prioritized_gaps: List of prioritized gaps
        max_items: Maximum number of items in plan
        
    Returns:
        Action plan list
    """
    plan = []
    
    for i, gap in enumerate(prioritized_gaps[:max_items], 1):
        action = {
            'rank': i,
            'category': gap.get('category'),
            'priority': gap.get('priority', 'medium'),
            'impact_score': gap.get('impact_score', 0)
        }
        
        # Generate specific action based on gap type
        if gap.get('type') == 'missing_page':
            action['action'] = 'Create new page'
            action['url_reference'] = gap.get('competitor_url')
            action['description'] = f"Create content similar to competitor page with {1-gap.get('similarity_score', 0):.1%} gap"
            
        elif gap.get('type') == 'thin_content':
            action['action'] = 'Expand content'
            action['url'] = gap.get('primary_url')
            action['description'] = f"Expand from {gap.get('primary_word_count', 0)} to ~{gap.get('competitor_word_count', 0)} words"
            
        elif gap.get('type') == 'metadata_gap':
            action['action'] = 'Fix metadata'
            action['url'] = gap.get('url')
            action['description'] = f"Add missing: {', '.join(gap.get('missing_elements', []))}"
            
        elif gap.get('type') == 'schema_gap':
            action['action'] = 'Add schema markup'
            action['url'] = gap.get('url')
            action['description'] = 'Implement structured data'
        
        plan.append(action)
    
    logger.info(f"Generated action plan with {len(plan)} items")
    return plan


def generate_summary(gaps: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Generate executive summary of gaps.
    
    Args:
        gaps: Dictionary of all gap types
        
    Returns:
        Summary dictionary
    """
    summary = {
        'total_gaps': 0,
        'by_category': {},
        'high_priority_count': 0,
        'estimated_effort': 'Medium'
    }
    
    for category, gap_list in gaps.items():
        count = len(gap_list)
        summary['total_gaps'] += count
        summary['by_category'][category] = count
        
        # Count high priority
        high_priority = sum(1 for g in gap_list if g.get('priority') == 'high')
        summary['high_priority_count'] += high_priority
    
    # Estimate effort
    if summary['total_gaps'] > 50:
        summary['estimated_effort'] = 'High'
    elif summary['total_gaps'] > 20:
        summary['estimated_effort'] = 'Medium'
    else:
        summary['estimated_effort'] = 'Low'
    
    return summary


def generate_quick_wins(prioritized_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Identify quick win opportunities.
    
    Args:
        prioritized_gaps: List of prioritized gaps
        
    Returns:
        List of quick win actions
    """
    quick_wins = []
    
    for gap in prioritized_gaps:
        is_quick_win = False
        
        # Metadata gaps are quick wins
        if gap.get('type') == 'metadata_gap':
            is_quick_win = True
        
        # Schema gaps are relatively quick
        if gap.get('type') == 'schema_gap':
            is_quick_win = True
        
        # High similarity missing pages might be quick adaptations
        if gap.get('type') == 'missing_page' and gap.get('similarity_score', 0) > 0.3:
            is_quick_win = True
        
        if is_quick_win:
            quick_wins.append(gap)
    
    # Limit to top 10 quick wins
    quick_wins = quick_wins[:10]
    
    logger.info(f"Identified {len(quick_wins)} quick wins")
    return quick_wins
