"""Markdown Mermaid Extension"""

import base64
import os
import platform
import re
import shutil
import subprocess
import tempfile
from typing import Generator, List

from markdown import Extension
from markdown.preprocessors import Preprocessor


class MermaidProcessor(Preprocessor):
    """Preprocessor to convert diagram code blocks to SVG/PNG image Data URIs."""

    DIAGRAM_BLOCK_START_RE = re.compile(r'^\s*```(?P<lang>mermaid)(?:\s+(?P<options>.+))?')
    DIAGRAM_BLOCK_END_RE = re.compile(r'^\s*```')

    MIME_TYPES = {
        'svg': 'image/svg+xml',
        'png': 'image/png',
    }
    IMG_TAG_ATTRIBUTES = [
        'alt',
        'width',
        'height',
        'class',
        'id',
        'style',
        'title',
    ]
    MERMAID_OPTIONS = [
        'theme',
        'width',
        'height',
        'backgroundColor',
        'svgId',
        'scale',
    ]

    def __init__(self, md, config):
        super().__init__(md)

    def run(self, lines: List[str]) -> List[str]:
        return list(self._parse_diagram_block(lines))

    def _parse_diagram_block(self, lines: List[str]) -> Generator:
        """Parse diagram code block"""
        is_in_diagram_block = False
        block_lines: List[str] = []

        for line in lines:
            if is_in_diagram_block:
                block_lines.append(line)
                if self.DIAGRAM_BLOCK_END_RE.match(line):
                    is_in_diagram_block = False
                    line = self._diagram_block_to_html(block_lines)
                    block_lines = []
                    yield line
            else:
                if self.DIAGRAM_BLOCK_START_RE.match(line):
                    is_in_diagram_block = True
                    block_lines.append(line)
                else:
                    yield line

    def _diagram_block_to_html(self, lines: List[str]) -> str:
        """Convert diagram code block to HTML"""
        diagram_code = ''
        html_string = ''

        for line in lines:
            diagram_match = re.search(self.DIAGRAM_BLOCK_START_RE, line)
            if diagram_match:
                options = diagram_match.group('options')
                code_block_options = {}
                if options:
                    for option in options.split():
                        key, _, value = option.partition('=')
                        code_block_options[key] = value
                continue

            elif re.search(self.DIAGRAM_BLOCK_END_RE, line):
                # Image format
                if 'format' in code_block_options:
                    format = code_block_options['format'].strip('"')
                    del code_block_options['format']
                    if format not in ['svg', 'png']:
                        format = 'svg'
                else:
                    format = 'svg'

                # img tag attributes and mermaid-cli options
                img_tag_attributes = {}
                mermaid_options = {}
                for option in code_block_options:
                    if option in self.IMG_TAG_ATTRIBUTES:
                        img_tag_attributes[option] = code_block_options[option]
                    if option in self.MERMAID_OPTIONS:
                        mermaid_options[option] = code_block_options[option].strip('"')

                img_src = self._get_img_src(diagram_code, format, mermaid_options)
                if img_src:
                    # Build the <img> tag with extracted options
                    img_tag = f'<img src="{img_src}"'
                    for key, value in img_tag_attributes.items():
                        img_tag += f' {key}={value}'
                    img_tag += ' />'
                    html_string = img_tag
                break

            else:
                diagram_code = diagram_code + '\n' + line

        return html_string

    def _get_img_src(self, diagram_code: str, format: str, mermaid_options: dict) -> str:
        """Convert mermaid code to SVG/PNG using mmdc (Mermaid CLI)."""
        base64image = self._get_base64image(diagram_code, format, mermaid_options)
        if base64image:
            return f'data:{self.MIME_TYPES[format]};base64,{base64image}'
        return ''

    def _get_base64image(self, diagram_code: str, format: str, mermaid_options: dict) -> str:
        """Convert mermaid code to SVG/PNG using mmdc (Mermaid CLI)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp_mmd:
            tmp_mmd.write(diagram_code)
            mmd_filepath = tmp_mmd.name

        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{format}', delete=False) as tmp_img:
            img_filepath = tmp_img.name

        mmdc_name = 'mmdc.cmd' if platform.system() == 'Windows' else 'mmdc'
        mmdc_path = os.path.join(os.getcwd(), 'node_modules/.bin', mmdc_name)
        if not shutil.which(mmdc_path):
            mmdc_path = mmdc_name

        options = []
        for key, value in mermaid_options.items():
            options.append(f'--{key}')
            options.append(value)

        try:
            command = [
                mmdc_path,
                '--input',
                mmd_filepath,
                '--output',
                img_filepath,
                '--outputFormat',
                format,
                '--puppeteerConfigFile',
                os.path.join(os.path.dirname(__file__), 'puppeteer-config.json'),
            ]

            command.extend(options)

            subprocess.run(command, check=True, capture_output=True)
            if format == 'svg':
                with open(img_filepath, 'r', encoding='utf-8') as f:
                    svg_content: str = f.read()
            elif format == 'png':
                with open(img_filepath, 'rb') as f:
                    png_content: bytes = f.read()
        except subprocess.CalledProcessError as e:
            print(f'Error generating SVG: {e.stderr.decode()}')
            return ''
        finally:
            os.remove(mmd_filepath)
            os.remove(img_filepath)

        if format == 'svg':
            base64image = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        else:
            base64image = base64.b64encode(png_content).decode('utf-8')

        return base64image


class MermaidExtension(Extension):
    """Markdown Extension to support Mermaid diagrams."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.extension_configs = kwargs

    def extendMarkdown(self, md):
        config = self.getConfigs()
        final_config = {**config, **self.extension_configs}
        mermaid_preprocessor = MermaidProcessor(md, final_config)
        md.preprocessors.register(mermaid_preprocessor, 'markdown_mermaid_cli', 50)


# pylint: disable=C0103
def makeExtension(**kwargs):
    """Create an instance of the MermaidExtension."""
    return MermaidExtension(**kwargs)
