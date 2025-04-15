"""Markdown Mermaid Extension"""

import base64
import os
import subprocess
import tempfile
from typing import List

from markdown import Extension
from markdown.preprocessors import Preprocessor


class MermaidDataURIPreprocessor(Preprocessor):
    """Preprocessor to convert mermaid code blocks to SVG images."""

    def __init__(self, config, md=None):
        self.config = config
        super().__init__(md)

    def run(self, lines: List[str]) -> List[str]:
        new_lines: List[str] = []
        is_in_mermaid = False

        for line in lines:
            if line.strip() == '```mermaid':
                is_in_mermaid = True
                mermaid_block: List[str] = []
                continue
            elif line.strip() == '```' and is_in_mermaid:
                is_in_mermaid = False
                if mermaid_block:
                    mermaid_code = '\n'.join(mermaid_block)
                    svg_content = self._mermaid2svg(mermaid_code)
                    if svg_content:
                        data_uri = self._svg2data_uri(svg_content)
                        new_lines.append(f'<img src="{data_uri}" alt="Mermaid diagram">')
                    else:
                        new_lines.append('```mermaid')
                        new_lines.extend(mermaid_block)
                        new_lines.append('```')
                continue

            if is_in_mermaid:
                mermaid_block.append(line)
            else:
                new_lines.append(line)

        return new_lines

    def _svg2data_uri(self, svg_content: str) -> str:
        """Convert SVG content to Data URI."""
        base64_svg = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        data_uri = f'data:image/svg+xml;base64,{base64_svg}'
        return data_uri

    def _mermaid2svg(self, mermaid_code: str) -> str:
        """Convert mermaid code to SVG using mmdc (Mermaid CLI)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp_mmd:
            tmp_mmd.write(mermaid_code)
            mmd_filepath = tmp_mmd.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.svg', delete=False) as tmp_svg:
            svg_filepath = tmp_svg.name

        try:
            command = [
                'mmdc',
                '--input',
                mmd_filepath,
                '--output',
                svg_filepath,
                '--puppeteerConfigFile',
                os.path.join(os.path.dirname(__file__), 'puppeteer-config.json'),
            ]
            subprocess.run(command, check=True, capture_output=True)
            with open(svg_filepath, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            return svg_content
        except subprocess.CalledProcessError as e:
            print(f'Error generating SVG: {e.stderr.decode()}')
            return ''
        finally:
            os.remove(mmd_filepath)
            os.remove(svg_filepath)


class MermaidDataURIExtension(Extension):
    """Markdown Extension to support Mermaid diagrams."""

    def extendMarkdown(self, md):
        config = self.getConfigs()
        mermaid_preprocessor = MermaidDataURIPreprocessor(config, md)
        md.preprocessors.register(mermaid_preprocessor, 'mermaid', 50)


# pylint: disable=C0103
def makeExtension(**kwargs):
    """Create an instance of the MermaidDataURIExtension."""
    return MermaidDataURIExtension(**kwargs)
