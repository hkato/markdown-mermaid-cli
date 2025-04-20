# [markdown-mermaid-cli](https://hkato.github.io/markdown-mermaid-cli/)

[Mermaid][mermaid] extension for [Python-Markdown][python-markdown] using [Mermaid-CLI][mermaid-cli].

This extension converts Mermaid diagram code blocks into Base64 encoded [data: URI][data-uri].
This enables PDF generation with tools like [MkDocs to PDF][mkdocs-to-pdf]/[WeasyPrint][wasyprint] without requiring JavaScript, even during web browsing.

[mermaid]: https://mermaid.js.org/
[python-markdown]: https://python-markdown.github.io/
[mermaid-cli]: https://github.com/mermaid-js/mermaid-cli
[data-uri]: https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data
[mkdocs-to-pdf]: https://mkdocs-to-pdf.readthedocs.io/
[wasyprint]: https://weasyprint.org/

## Install

```sh
pip install markdown-mermaid-cli
```

## Requirements

### Mermaid CLI

```sh
npm install @mermaid-js/mermaid-cli
```

or

```sh
npm install --global @mermaid-js/mermaid-cli
```

## Usage

````python
import markdown
from markdown_mermaid_cli import MermaidExtension

markdown_text = """```mermaid
sequenceDiagram
    participant Alice
    participant Bob
    Bob->>Alice: Hi Alice
    Alice->>Bob: Hi Bob
```"""

html_output = markdown.markdown(
    markdown_text, extensions=[MermaidExtension()]
)

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
  - markdown_mermaid_cli
```

## Diagram

```mermaid
sequenceDiagram
    participant application as Application<br/>(eg MkDocs)
    participant markdown as Python Markdown
    participant extension as MermaidDataURIExtension
    participant engine as Mermaid CLI

    application->>markdown: Markdown + Mermaid
    markdown->>extension: Preprocessor
    extension->>engine: Mermaid
    engine-->>engine: Convert
    engine-->>extension: Image Data
    extension-->>extension: Base64 encode
    extension-->>markdown: Markdown + data URI image
    markdown-->>application: HTML + data URI image
```
