"""Open-source model backend (Qwen/Qwen2.5-7B-Instruct).

The app's reasoning engine is an open-source, open-weights model
served from Hugging Face. The model is loaded LAZILY and ONLY at a
commit SHA pinned in the configuration — never at a floating branch
or tag. The configuration holds the placeholder "to be pinned at
build time" until the SHA is resolved via the TOOL-GH-01 flow
(pin_commit_sha / verify_ref); this module never invents a SHA.

The model is a reasoning engine only. It never assigns
VERIFIED_FACT: its outputs are labelled GENERATED_ANALYSIS (and the
underlying claims stay SOURCE_REPORTED) until a human reviews them.

No weights are ever downloaded by this app: loading uses
local_files_only=True, so weights must already be present in the
local Hugging Face cache at the pinned revision. If Transformers is
not installed, or the weights are not cached, load() fails cleanly
with a clear message.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

DEFAULT_MODEL_REPO = "Qwen/Qwen2.5-7B-Instruct"
DEFAULT_MODEL_LICENSE = "Apache-2.0"
UNPINNED_SHA = "to be pinned at build time"

_SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")


class ModelUnavailable(RuntimeError):
    """The model backend cannot be used (not pinned, not installed,
    or weights not available locally)."""


@dataclass(frozen=True)
class ModelConfig:
    repo: str = DEFAULT_MODEL_REPO
    sha: str = UNPINNED_SHA
    license: str = DEFAULT_MODEL_LICENSE

    @property
    def is_pinned(self) -> bool:
        """True only when sha is a 40-hex commit SHA."""
        return isinstance(self.sha, str) and _SHA_RE.match(self.sha) is not None

    def to_dict(self) -> dict:
        return {"repo": self.repo, "sha": self.sha,
                "license": self.license}


def _parse_simple_yaml(text: str) -> dict:
    """Minimal parser for the flat config file (nested mappings,
    lists of scalars, lists of one-level mappings). No PyYAML needed,
    so the core stays stdlib-only. Raises ValueError on structure it
    cannot represent."""
    root: dict = {}
    # Stack of (key_indent, container): key_indent is the indent at
    # which keys/items belonging to the container appear. The root
    # never pops (indent -1).
    stack: list[tuple[int, object]] = [(-1, root)]
    # A "key:" line with no value leaves a pending nested container,
    # decided by the next line: a list item means a list, a deeper
    # key means a mapping, anything else means an empty mapping.
    pending: tuple[dict, str, int] | None = None

    def resolve_pending(next_indent: int, is_list_item: bool) -> None:
        nonlocal pending
        if pending is None:
            return
        parent, key, key_indent = pending
        pending = None
        if next_indent > key_indent:
            parent[key] = [] if is_list_item else {}
            stack.append((next_indent, parent[key]))
        else:
            parent[key] = {}

    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        content = raw.strip()
        is_list_item = content.startswith("- ")
        while len(stack) > 1 and stack[-1][0] > indent:
            stack.pop()
        resolve_pending(indent, is_list_item)
        container = stack[-1][1]
        if is_list_item:
            if not isinstance(container, list):
                raise ValueError("list item without a list container")
            item = content[2:].strip()
            if ":" in item and not item.startswith(("'", '"')):
                key, _, value = item.partition(":")
                entry = {key.strip(): _scalar(value.strip())}
                container.append(entry)
                stack.append((indent + 2, entry))
            else:
                container.append(_scalar(item))
            continue
        if ":" not in content:
            continue
        if not isinstance(container, dict):
            raise ValueError("mapping key without a mapping container")
        key, _, value = content.partition(":")
        key = key.strip()
        value = value.strip()
        if value == "":
            pending = (container, key, indent)
        else:
            container[key] = _scalar(value)
    resolve_pending(-1, False)
    return root


def _scalar(value: str):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    if value.lower() in ("true", "false"):
        return value.lower() == "true"
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def load_config(path: str | Path | None = None) -> ModelConfig:
    """Load the model section of a config file (config.yaml, or
    config.example.yaml). Missing file or missing section returns
    the defaults (unpinned)."""
    target = Path(path) if path is not None else None
    if target is None:
        here = Path(__file__).resolve().parent.parent
        for name in ("config.yaml", "config.example.yaml"):
            candidate = here / name
            if candidate.is_file():
                target = candidate
                break
    if target is None or not target.is_file():
        return ModelConfig()
    parsed = _parse_simple_yaml(target.read_text(encoding="utf-8"))
    model = parsed.get("model", {}) if isinstance(parsed, dict) else {}
    if not isinstance(model, dict):
        model = {}
    return ModelConfig(
        repo=str(model.get("repo", DEFAULT_MODEL_REPO)),
        sha=str(model.get("sha", UNPINNED_SHA)),
        license=str(model.get("license", DEFAULT_MODEL_LICENSE)),
    )


class ModelBackend:
    """Lazy backend for the open-source model.

    Nothing is imported or loaded at construction time. Call
    available() for a safe status check, load() to load weights
    (raises ModelUnavailable with a clear reason when it cannot),
    and generate() to produce labelled output.
    """

    def __init__(self, config: ModelConfig | None = None) -> None:
        self.config = config or ModelConfig()
        self._tokenizer = None
        self._model = None
        self._loaded = False

    def available(self) -> tuple[bool, str]:
        """(available, reason). Never raises, never loads anything."""
        if not self.config.is_pinned:
            return (False,
                    "model commit SHA is not pinned: the configuration "
                    "holds the placeholder 'to be pinned at build time'. "
                    "Resolve and pin the SHA at build time via the "
                    "TOOL-GH-01 flow (pin_commit_sha / verify_ref) "
                    "before the model can load.")
        try:
            import transformers  # noqa: F401  (import check only)
        except ImportError:
            return (False,
                    "Hugging Face Transformers is not installed. "
                    "Install it (pip install transformers torch) to "
                    "enable the model backend.")
        return (True,
                "Transformers is installed and the model SHA is pinned; "
                "weights must already be present in the local Hugging "
                "Face cache at the pinned revision (this app never "
                "downloads weights).")

    def load(self):
        """Load the tokenizer and weights at the pinned SHA.

        Raises ModelUnavailable when the SHA is not pinned, when
        Transformers is missing, or when the weights are not
        available locally. Never downloads weights.
        """
        if self._loaded:
            return self
        if not self.config.is_pinned:
            raise ModelUnavailable(
                "cannot load model: commit SHA is not pinned. The "
                "configuration holds the placeholder 'to be pinned at "
                "build time'. Resolve and pin the SHA at build time "
                "via the TOOL-GH-01 flow (pin_commit_sha to resolve "
                "the ref, verify_ref to check it), record it in the "
                "app configuration, and try again.")
        try:
            from transformers import (  # type: ignore
                AutoModelForCausalLM, AutoTokenizer)
        except ImportError as exc:
            raise ModelUnavailable(
                "cannot load model: Hugging Face Transformers is not "
                "installed. Install it (pip install transformers "
                "torch) to enable the model backend.") from exc
        try:
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.config.repo, revision=self.config.sha,
                local_files_only=True, trust_remote_code=False)
            self._model = AutoModelForCausalLM.from_pretrained(
                self.config.repo, revision=self.config.sha,
                local_files_only=True, trust_remote_code=False)
        except Exception as exc:  # noqa: BLE001 — report, don't crash
            raise ModelUnavailable(
                "cannot load model: weights for "
                f"{self.config.repo} at the pinned revision are not "
                "available locally. This app never downloads weights; "
                "fetch them once with the pinned SHA (for example "
                "with huggingface-cli download --revision <sha>) and "
                f"try again. Underlying error: {exc}") from exc
        self._loaded = True
        return self

    def generate(self, prompt: str, max_new_tokens: int = 256) -> dict:
        """Generate text for a prompt. Returns a dict with the text
        and its epistemic label. The output is always
        GENERATED_ANALYSIS; it never carries VERIFIED_FACT."""
        self.load()
        inputs = self._tokenizer(prompt, return_tensors="pt")
        outputs = self._model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=False)
        text = self._tokenizer.decode(
            outputs[0][inputs["input_ids"].shape[1]:],
            skip_special_tokens=True)
        return {
            "text": text.strip(),
            "epistemic_tag": "GENERATED_ANALYSIS",
            "model": self.config.repo,
            "sha": self.config.sha,
        }

    @property
    def loaded(self) -> bool:
        return self._loaded
