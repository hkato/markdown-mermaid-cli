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
            if line.strip().startswith('```mermaid'):
                is_in_mermaid = True
                mermaid_block: List[str] = []
                # Extract options after '```mermaid'
                options = line.strip()[10:].strip()
                option_dict = {}
                if options:
                    for option in options.split():
                        key, _, value = option.partition('=')
                        option_dict[key] = value
                continue
            elif line.strip() == '```' and is_in_mermaid:
                is_in_mermaid = False
                if mermaid_block:
                    mermaid_code = '\n'.join(mermaid_block)

                    # Image type handling
                    if 'image' in option_dict:
                        image_type = option_dict['image']
                        del option_dict['image']
                        if image_type not in ['svg', 'png']:
                            image_type = 'svg'
                    else:
                        image_type = 'svg'

                    base64image = self._mermaid2base64image(mermaid_code, image_type)
                    if base64image:
                        # Build the <img> tag with extracted options
                        if image_type == 'svg':
                            img_tag = f'<img src="data:image/svg+xml;base64,{base64image}"'
                        else:
                            img_tag = f'<img src="data:image/png;base64,{base64image}"'
                        for key, value in option_dict.items():
                            img_tag += f' {key}={value}'
                        img_tag += ' />'
                        new_lines.append(img_tag)
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

    def _mermaid2base64image(self, mermaid_code: str, image_type: str) -> str:
        """Convert mermaid code to SVG using mmdc (Mermaid CLI)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp_mmd:
            tmp_mmd.write(mermaid_code)
            mmd_filepath = tmp_mmd.name

        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{image_type}', delete=False) as tmp_img:
            img_filepath = tmp_img.name

        try:
            command = [
                'mmdc',
                '--input',
                mmd_filepath,
                '--output',
                img_filepath,
                '--outputFormat',
                image_type,
                '--puppeteerConfigFile',
                os.path.join(os.path.dirname(__file__), 'puppeteer-config.json'),
            ]
            subprocess.run(command, check=True, capture_output=True)
            if image_type == 'svg':
                with open(img_filepath, 'r', encoding='utf-8') as f:
                    svg_content: str = f.read()
            elif image_type == 'png':
                with open(img_filepath, 'rb') as f:
                    png_content: bytes = f.read()
        except subprocess.CalledProcessError as e:
            print(f'Error generating SVG: {e.stderr.decode()}')
            return ''
        finally:
            os.remove(mmd_filepath)
            os.remove(img_filepath)

        if image_type == 'svg':
            base64image = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        else:
            base64image = base64.b64encode(png_content).decode('utf-8')

        return base64image


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
