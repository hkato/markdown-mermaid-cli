"""Markdown Mermaid Extension"""

import base64
import os
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as etree

import requests
from markdown import Extension
from markdown.blockprocessors import BlockProcessor


class MermaidDataURIProcessor(BlockProcessor):
    """Preprocessor to convert mermaid code blocks to SVG/PNG images."""

    MERMAID_CODE_BLOCK_RE = re.compile(r'```mermaid\s*(.*)')
    MIME_TYPES = {
        'svg': 'image/svg+xml',
        'png': 'image/png',
    }

    def test(self, parent, block):
        return self.MERMAID_CODE_BLOCK_RE.match(block)

    def __init__(self, parser, kroki_url, mermaid_cli):
        super().__init__(parser)
        self.kroki_url = kroki_url
        self.mermaid_cli = mermaid_cli

    def run(self, parent, blocks):
        # Mermaid code block
        block = blocks.pop(0)
        match = self.MERMAID_CODE_BLOCK_RE.match(block)
        mermaid_code = block[match.end() :].strip().replace('```', '').strip()

        # Options
        options_str = match.group(1).strip()
        options = {}
        if options_str:
            for item in options_str.split():
                if '=' in item:
                    key, value = item.split('=', 1)
                    options[key] = value.strip('"\'')

        # Data URI
        data_uri = self._get_data_uri(mermaid_code, options)

        # Create image element
        el = etree.SubElement(parent, 'p')
        img = etree.SubElement(el, 'img', {'src': data_uri})
        img.text = mermaid_code
        del options['image']
        for key, value in options.items():
            img.set(key, value)

    def _get_data_uri(self, content: str, options: dict) -> str:
        """Convert mermaid code to data URI."""
        image_type = options.get('image', 'svg')
        base64image = self._get_base64image(content, image_type)
        data_uri = f'data:{self.MIME_TYPES[image_type]};base64,{base64image}'
        return data_uri

    def _get_base64image(self, mermaid_code: str, image_type: str) -> str:
        """Convert mermaid code to SVG/PNG."""
        if not self.mermaid_cli:
            return self._get_base64image_from_kroki(mermaid_code, image_type)
        else:
            return self._get_base64image_from_mmdc(mermaid_code, image_type)

    def _get_base64image_from_kroki(self, mermaid_code: str, image_type: str) -> str:
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

    def _get_base64image_from_mmdc(self, mermaid_code: str, image_type: str) -> str:
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
            'kroki_url': [kwargs.get('kroki_url', 'https://kroki.io'), 'Kroki server URL'],
            'mermaid_cli': [kwargs.get('mermaid_cli', False), 'Use mermaid CLI (requires installation)'],
        }
        super().__init__(**kwargs)

    def extendMarkdown(self, md):
        self.processor = MermaidDataURIProcessor(md.parser, self.getConfig('kroki_url'), self.getConfig('mermaid_cli'))
        md.parser.blockprocessors.register(self.processor, 'markdown_mermaid_data_uri', 50)


# pylint: disable=C0103
def makeExtension(**kwargs):
    """Create an instance of the MermaidDataURIExtension."""
    return MermaidDataURIExtension(**kwargs)
