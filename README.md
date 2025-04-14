# markdown-mermaid-cli

[Mermaid](https://mermaid.js.org/) extension for [Python-Markdown](https://python-markdown.github.io/) using [mermaid-cli](https://github.com/mermaid-js/mermaid-cli).

Mermaid code blocks are converted to SVG and treated as [data: URLs](https://developer.mozilla.org/en-US/docs/Web/URI/Reference/Schemes/data). This allows for PDF generation with tools like [WeasyPrint](https://weasyprint.org/) without the need for JavaScript, even during web browsing.

## Install

```sh
pip install git+https://github.com/hkato/markdown-mermaid-cli.git
```

```sh
npm install -g @mermaid-js/mermaid-cli
```

## Usage

````python
import markdown
from markdown_mermaid_cli.extension import MermaidCLIExtension

markdown_text = """```mermaid
sequenceDiagram
    participant Alice
    participant Bob
    Alice->>John: Hello John, how are you?
    loop HealthCheck
        John->>John: Fight against hypochondria
    end
    Note right of John: Rational thoughts <br/>prevail!
    John-->>Alice: Great!
    John->>Bob: How about you?
    Bob-->>John: Jolly good!
```"""

html_output = markdown.markdown(markdown_text, extensions=[MermaidCLIExtension()])
print(html_output)
````

```html
<p><img src="data:image/svg+xml;base64,PHN2ZyBhcmlhLXJvbGVkZXNjcmlwdGlvbj0ic2VxdWVuY2UiIHJvbGU9ImdyYXBoaWNzLWRvY3VtZW5
0IGRvY3VtZW50IiB2aWV3Qm94PSItNTAgLTEwIDc1MCA1NzQiIHN0eWxlPSJtYXgtd2lkdGg6IDc1MHB4OyBiYWNrZ3JvdW5kLWNvbG9yOiB3aGl0ZTsiI
...
...
...
8L3N2Zz4=" alt="Mermaid diagram"></p>
```

## MkDocs Integration

```yaml
# mkdocs.yml
markdown_extensions:
  - markdown_mermaid_cli
```
