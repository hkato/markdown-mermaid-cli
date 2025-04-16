# markdown-mermaid-data-uri

[Mermaid](https://mermaid.js.org/) extension for [Python-Markdown](https://python-markdown.github.io/) using [mermaid-cli](https://github.com/mermaid-js/mermaid-cli).

Mermaid code blocks are converted to SVG/PNG and treated as [data: URI](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data). This allows for PDF generation with tools like [WeasyPrint](https://weasyprint.org/) without the need for JavaScript, even during web browsing.

## Install

```sh
pip install git+https://github.com/hkato/markdown-mermaid-data-uri.git
```

```sh
npm install @mermaid-js/mermaid-cli
```

## Usage

````python
import markdown
from mermaid_data_uri.extension import MermaidDataURIExtension

markdown_text = """```mermaid
sequenceDiagram
    participant Alice
    participant Bob
    Bob->>Alice: Hi Alice
    Alice->>Bob: Hi Bob
```"""

html_output = markdown.markdown(markdown_text, extensions=[MermaidDataURIExtension()])
print(html_output)
````

```html
<p><img src="data:image/svg+xml;base64,PHN2ZyBhcmlhLXJvbGVkZXNjcmlwdGlvbj0ic2VxdWVuY2UiIHJvbGU
9ImdyYXBoaWNzLWRvY3VtZW50IGRvY3VtZW50IiB2aWV3Qm94PSItNTAgLTEwIDc1MCA1NzQiIHN0eWxlPSJtYXgtd2lkd
Gg6IDc1MHB4OyBiYWNrZ3JvdW5kLWNvbG9yOiB3aGl0ZTsiIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9yZy8xOTk
...
...
...
IHgxPSIyNzYiLz48L3N2Zz4=" ></p>
```

## MkDocs Integration

```yaml
# mkdocs.yml
markdown_extensions:
  - mermaid_data_uri
```

## Diagram

```mermaid
sequenceDiagram
    participant application as Application<br/>(eg MkDocs)
    participant markdown as Python Markdown
    participant extension as MermaidDataURIExtension
    participant mmdc as Mermaid CLI

    application->>markdown: Markdown + Mermaid
    markdown->>extension: Preprocessor
    extension->>mmdc: Mermaid
    mmdc-->>mmdc: Convert
    mmdc-->>extension: Image Data
    extension-->>extension: Base64 encode
    extension-->>markdown: Markdown + data URI image
    markdown-->>application: HTML + data URI image
```
