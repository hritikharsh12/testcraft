from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

_TEMPLATES_DIR = Path(__file__).parent / "templates"

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(disabled_extensions=("jinja",)),  # this is a text prompt, not HTML
    trim_blocks=True,
    lstrip_blocks=True,
)


def build_prompt(template_name: str, **context) -> str:
    template = _env.get_template(template_name)
    return template.render(**context)
