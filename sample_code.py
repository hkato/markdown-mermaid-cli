import os

import markdown
from markdown_mermaid_cli import MermaidExtension

markdown_text = """
# Sample Markdown with Mermaid Diagram

## Mermaid Diagram

```mermaid format=svg width=500 alt="sequenceDiagram" theme="forest" backgroundColor="#dcdcdc"
sequenceDiagram
    participant Alice
    participant Bob
    Bob->>Alice: Hi Alice
    Alice->>Bob: Hi Bob
```
"""

html_output = markdown.markdown(markdown_text, extensions=[MermaidExtension()])

with open(os.path.splitext(__file__)[0] + '.html', 'w') as f:
    f.write(html_output)
