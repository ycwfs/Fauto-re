"""
Paper writing service - generates academic papers section by section.
"""
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add Auto-Research to path
AUTO_RESEARCH_PATH = Path("/data1/data1/wfs/misc/Auto-Research")
sys.path.insert(0, str(AUTO_RESEARCH_PATH))

from src.automation.cli_runner import build_cli_command, detect_cli_type
from src.utils.user_data import get_user_data_dir
from src.config import settings


class PaperWriter:
    """Generates academic papers using AI CLI."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user_dir = get_user_data_dir(user_id)
        self.papers_dir = self.user_dir / "written_papers"
        self.papers_dir.mkdir(exist_ok=True)

    def generate_outline(self, title: str, abstract: str, venue: str = "NeurIPS") -> Dict[str, Any]:
        """
        Generate paper outline based on title and abstract.

        Args:
            title: Paper title
            abstract: Paper abstract
            venue: Target venue (NeurIPS, ICML, ACL, etc.)

        Returns:
            dict: Outline with sections
        """
        prompt = f"""Generate a detailed outline for an academic paper with the following details:

Title: {title}
Abstract: {abstract}
Target Venue: {venue}

Please provide a structured outline with:
1. Introduction (with subsections)
2. Related Work
3. Method/Approach (with subsections)
4. Experiments (with subsections)
5. Results and Discussion
6. Conclusion
7. Future Work (optional)

For each section, provide:
- Section title
- Key points to cover
- Estimated length (in paragraphs)

Output as JSON with this structure:
{{
  "sections": [
    {{
      "title": "Introduction",
      "subsections": [...],
      "key_points": [...],
      "estimated_paragraphs": 3
    }},
    ...
  ]
}}
"""

        # Build CLI command
        cli_type = detect_cli_type(settings.copilot_command)
        cmd = build_cli_command(
            cli_type=cli_type,
            command=settings.copilot_command,
            prompt=prompt,
            model=settings.cli_model,
            reasoning_effort=settings.cli_reasoning_effort,
        )

        # Run CLI
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )

        # Parse output
        output = result.stdout
        try:
            # Extract JSON from output
            start = output.find("{")
            end = output.rfind("}") + 1
            if start >= 0 and end > start:
                outline_data = json.loads(output[start:end])
                return {
                    "status": "success",
                    "outline": outline_data,
                }
        except json.JSONDecodeError:
            pass

        return {
            "status": "error",
            "message": "Failed to parse outline",
            "output": output,
        }

    def generate_section(
        self,
        section_title: str,
        key_points: List[str],
        context: Dict[str, Any],
        previous_sections: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Generate content for a specific section.

        Args:
            section_title: Title of the section
            key_points: Key points to cover
            context: Paper context (title, abstract, experiment results, etc.)
            previous_sections: Previously generated sections for context

        Returns:
            dict: Generated section content
        """
        prompt = f"""Write the "{section_title}" section for an academic paper.

Paper Title: {context.get('title', 'N/A')}
Abstract: {context.get('abstract', 'N/A')}

Key points to cover:
{chr(10).join(f"- {point}" for point in key_points)}

"""

        if previous_sections:
            prompt += f"\nPrevious sections for context:\n{previous_sections}\n"

        if context.get('experiment_results'):
            prompt += f"\nExperiment Results:\n{context['experiment_results']}\n"

        prompt += """
Please write this section in academic style:
- Use formal language
- Include proper citations (use [Author et al., Year] format)
- Be concise and clear
- Follow standard academic writing conventions
- Include technical details where appropriate

Output the section content in Markdown format.
"""

        # Build CLI command
        cli_type = detect_cli_type(settings.copilot_command)
        cmd = build_cli_command(
            cli_type=cli_type,
            command=settings.copilot_command,
            prompt=prompt,
            model=settings.cli_model,
            reasoning_effort=settings.cli_reasoning_effort,
        )

        # Run CLI
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        content = result.stdout.strip()

        return {
            "status": "success",
            "section_title": section_title,
            "content": content,
        }

    def convert_to_latex(self, markdown_content: str, template: str = "neurips") -> Dict[str, Any]:
        """
        Convert Markdown content to LaTeX.

        Args:
            markdown_content: Paper content in Markdown
            template: LaTeX template (neurips, icml, acl, etc.)

        Returns:
            dict: LaTeX content
        """
        prompt = f"""Convert the following Markdown paper content to LaTeX format using the {template} template.

Markdown Content:
{markdown_content}

Please:
1. Use proper LaTeX commands and environments
2. Format equations with \\begin{{equation}}...\\end{{equation}}
3. Format citations with \\cite{{...}}
4. Include proper section commands (\\section, \\subsection, etc.)
5. Format figures with \\begin{{figure}}...\\end{{figure}}
6. Format tables with \\begin{{table}}...\\end{{table}}

Output only the LaTeX content (document body, not the full preamble).
"""

        # Build CLI command
        cli_type = detect_cli_type(settings.copilot_command)
        cmd = build_cli_command(
            cli_type=cli_type,
            command=settings.copilot_command,
            prompt=prompt,
            model=settings.cli_model,
            reasoning_effort=settings.cli_reasoning_effort,
        )

        # Run CLI
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )

        latex_content = result.stdout.strip()

        return {
            "status": "success",
            "latex_content": latex_content,
        }

    def save_paper(
        self,
        paper_id: int,
        title: str,
        content: str,
        format: str = "markdown",
    ) -> Dict[str, Any]:
        """
        Save paper to file.

        Args:
            paper_id: Paper ID
            title: Paper title
            content: Paper content
            format: Format (markdown or latex)

        Returns:
            dict: Save result with file path
        """
        # Create paper directory
        paper_dir = self.papers_dir / f"paper_{paper_id}"
        paper_dir.mkdir(exist_ok=True)

        # Save content
        ext = "md" if format == "markdown" else "tex"
        filename = f"{title.replace(' ', '_').lower()}.{ext}"
        filepath = paper_dir / filename

        with open(filepath, "w") as f:
            f.write(content)

        return {
            "status": "success",
            "paper_id": paper_id,
            "filepath": str(filepath),
            "format": format,
        }
