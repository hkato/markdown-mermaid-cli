"""Markdown Mermaid Extension"""

import base64
import os
import shutil
import subprocess
import tempfile
from typing import List

import requests
from markdown import Extension
from markdown.preprocessors import Preprocessor


class MermaidDataURIPreprocessor(Preprocessor):
    """Preprocessor to convert mermaid code blocks to SVG/PNG images."""

    KROKI_URL = 'https://kroki.io'

    def __init__(self, md, config):
        super().__init__(md)
        self.kroki_url = config.get('kroki_url', self.KROKI_URL)
        self.mermaid_cli = config.get('mermaid_cli', False)

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
        """Convert mermaid code to SVG/PNG."""
        # Use Kroki or mmdc (Mermaid CLI) to convert mermaid code to image
        if not self.mermaid_cli:
            return self._mermaid2base64image_kroki(mermaid_code, image_type)
        else:
            return self._mermaid2base64image_mmdc(mermaid_code, image_type)

    def _mermaid2base64image_kroki(self, mermaid_code: str, image_type: str) -> str:
        """Convert mermaid code to SVG/PNG using Kroki."""
        kroki_url = f'{self.kroki_url}/mermaid/{image_type}'
        headers = {'Content-Type': 'text/plain'}
        response = requests.post(kroki_url, headers=headers, data=mermaid_code, timeout=30)
        if response.status_code == 200:
            if image_type == 'svg':
                body = response.content.decode('utf-8')
                base64image = base64.b64encode(body.encode('utf-8')).decode('utf-8')
                return base64image
            if image_type == 'png':
                body = response.content
                base64image = base64.b64encode(body).decode('utf-8')
                return base64image
        return ''

    def _mermaid2base64image_mmdc(self, mermaid_code: str, image_type: str) -> str:
        """Convert mermaid code to SVG/PNG using mmdc (Mermaid CLI)."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.mmd', delete=False) as tmp_mmd:
            tmp_mmd.write(mermaid_code)
            mmd_filepath = tmp_mmd.name

        with tempfile.NamedTemporaryFile(mode='w', suffix=f'.{image_type}', delete=False) as tmp_img:
            img_filepath = tmp_img.name

        mmdc_path = os.path.join(os.getcwd(), 'node_modules/.bin/mmdc')
        if not shutil.which(mmdc_path):
            mmdc_path = 'mmdc'

        try:
            command = [
                mmdc_path,
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

    def __init__(self, **kwargs):
        self.config = {
            'kroki_url': ['https://kroki.io', 'Base URL for the Kroki server.'],
            'mermaid_cli': [False, 'Use mmdc (Mermaid CLI) instead of Kroki server.'],
        }
        super().__init__(**kwargs)
        self.extension_configs = kwargs

    def extendMarkdown(self, md):
        config = self.getConfigs()
        final_config = {**config, **self.extension_configs}
        mermaid_preprocessor = MermaidDataURIPreprocessor(md, final_config)
        md.preprocessors.register(mermaid_preprocessor, 'markdown_mermaid_data_udi', 50)


# pylint: disable=C0103
def makeExtension(**kwargs):
    """Create an instance of the MermaidDataURIExtension."""
    return MermaidDataURIExtension(**kwargs)
