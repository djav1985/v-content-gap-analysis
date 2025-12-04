"""Generate Markdown format gap analysis report."""
from datetime import datetime
from typing import Dict, Any
from pathlib import Path
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_markdown_report(
    gaps: Dict[str, Any],
    summary: Dict[str, Any],
    action_plan: list[Dict[str, Any]],
    quick_wins: list[Dict[str, Any]],
    config: Dict[str, Any],
    output_path: str = "reports/gap_report.md"
) -> None:
    """
    Generate comprehensive Markdown report.
    
    Args:
        gaps: All detected gaps
        summary: Executive summary
        action_plan: Prioritized action plan
        quick_wins: Quick win opportunities
        config: Configuration used
        output_path: Output file path
    """
    # Build markdown content
    md_lines = [
        "# SEO Content Gap Analysis Report",
        "",
        f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Primary Site:** {config.get('site', 'Unknown')}",
        f"**Competitors Analyzed:** {len(config.get('competitors', []))}",
        "",
        "---",
        "",
        "## Executive Summary",
        "",
        f"- **Total Gaps Identified:** {summary.get('total_gaps', 0)}",
        f"- **High Priority Items:** {summary.get('high_priority_count', 0)}",
        f"- **Estimated Effort:** {summary.get('estimated_effort', 'Unknown')}",
        "",
        "### Gaps by Category",
        ""
    ]
    
    for category, count in summary.get('by_category', {}).items():
        md_lines.append(f"- **{category.replace('_', ' ').title()}:** {count}")
    
    md_lines.extend([
        "",
        "---",
        "",
        "## Quick Wins (Top 10)",
        "",
        "These are high-impact, low-effort improvements you can make immediately:",
        ""
    ])
    
    for i, win in enumerate(quick_wins[:10], 1):
        md_lines.append(f"### {i}. {win.get('category', 'Unknown')}")
        md_lines.append("")
        
        if win.get('type') == 'metadata_gap':
            md_lines.append(f"**URL:** {win.get('url', 'N/A')}")
            md_lines.append(f"**Missing Elements:** {', '.join(win.get('missing_elements', []))}")
            md_lines.append("**Action:** Add missing metadata elements")
        
        elif win.get('type') == 'schema_gap':
            md_lines.append(f"**URL:** {win.get('url', 'N/A')}")
            md_lines.append("**Action:** Implement schema.org structured data")
        
        elif win.get('type') == 'missing_page':
            md_lines.append(f"**Competitor URL:** {win.get('competitor_url', 'N/A')}")
            md_lines.append(f"**Similarity Score:** {win.get('similarity_score', 0):.2%}")
            md_lines.append("**Action:** Create similar content")
        
        md_lines.append("")
    
    md_lines.extend([
        "---",
        "",
        "## Prioritized Action Plan",
        "",
        "Complete roadmap for addressing all gaps:",
        ""
    ])
    
    for action in action_plan[:20]:
        md_lines.append(f"### {action.get('rank')}. {action.get('action', 'Unknown Action')}")
        md_lines.append("")
        md_lines.append(f"- **Category:** {action.get('category', 'Unknown')}")
        md_lines.append(f"- **Priority:** {action.get('priority', 'medium').upper()}")
        md_lines.append(f"- **Impact Score:** {action.get('impact_score', 0):.1f}")
        
        if action.get('url'):
            md_lines.append(f"- **URL:** {action['url']}")
        if action.get('url_reference'):
            md_lines.append(f"- **Reference:** {action['url_reference']}")
        
        md_lines.append(f"- **Description:** {action.get('description', 'No description')}")
        md_lines.append("")
    
    md_lines.extend([
        "---",
        "",
        "## Detailed Gap Analysis",
        ""
    ])
    
    # Missing Pages
    if gaps.get('missing_pages'):
        md_lines.extend([
            "### Missing Content Pages",
            "",
            "Competitor pages with no similar content on your site:",
            ""
        ])
        
        for gap in gaps['missing_pages'][:15]:
            md_lines.append(f"- **Competitor URL:** {gap.get('competitor_url', 'N/A')}")
            md_lines.append(f"  - Similarity to closest match: {gap.get('similarity_score', 0):.2%}")
            md_lines.append(f"  - Closest match: {gap.get('closest_match_url', 'N/A')}")
            md_lines.append(f"  - Priority: {gap.get('priority', 'medium').upper()}")
            md_lines.append("")
    
    # Thin Content
    if gaps.get('thin_content'):
        md_lines.extend([
            "### Thin Content Pages",
            "",
            "Your pages that are significantly shorter than competitor equivalents:",
            ""
        ])
        
        for gap in gaps['thin_content'][:15]:
            md_lines.append(f"- **Your URL:** {gap.get('primary_url', 'N/A')}")
            md_lines.append(f"  - Your word count: {gap.get('primary_word_count', 0)}")
            md_lines.append(f"  - Competitor word count: {gap.get('competitor_word_count', 0)}")
            md_lines.append(f"  - Ratio: {gap.get('ratio', 0):.1f}x")
            md_lines.append(f"  - Competitor reference: {gap.get('competitor_url', 'N/A')}")
            md_lines.append("")
    
    # Metadata Gaps
    if gaps.get('metadata_gaps'):
        md_lines.extend([
            "### Metadata Issues",
            "",
            "Pages with missing or incomplete metadata:",
            ""
        ])
        
        for gap in gaps['metadata_gaps'][:15]:
            md_lines.append(f"- **URL:** {gap.get('url', 'N/A')}")
            md_lines.append(f"  - Missing: {', '.join(gap.get('missing_elements', []))}")
            md_lines.append("")
    
    # Schema Gaps
    if gaps.get('schema_gaps'):
        md_lines.extend([
            "### Schema Markup Missing",
            "",
            "Pages that should have structured data:",
            ""
        ])
        
        for gap in gaps['schema_gaps'][:15]:
            md_lines.append(f"- {gap.get('url', 'N/A')}")
        md_lines.append("")
    
    md_lines.extend([
        "---",
        "",
        "## Configuration Used",
        "",
        f"- **Similarity Threshold:** {config.get('similarity_threshold', 0.45)}",
        f"- **Chunk Size:** {config.get('chunk_size', 1500)} tokens",
        f"- **Thin Content Ratio:** {config.get('thin_content_ratio', 3.0)}x",
        "",
        "---",
        "",
        "## Next Steps",
        "",
        "1. Review and validate the quick wins",
        "2. Assign resources to high-priority items",
        "3. Create content briefs for missing pages",
        "4. Schedule metadata and schema updates",
        "5. Plan content expansion for thin pages",
        "",
        "---",
        "",
        f"*Report generated by SEO Gap Analysis Agent v1.0*"
    ])
    
    # Write markdown file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    logger.info(f"Markdown report saved to {output_path}")
