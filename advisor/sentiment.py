"""
advisor/sentiment.py - FinBERT sentiment scoring for financial text.

Uses ProsusAI/finbert (3-class {positive, negative, neutral}, ~440MB, MIT license)
to produce a signed score in [-1, +1] where:
  * label="positive" -> score = +confidence
  * label="negative" -> score = -confidence
  * label="neutral"  -> score = 0.0

The model is lazy-loaded on first use (~5s cold start on CPU).

CLI:
    python -m advisor.sentiment "Reliance beats Q4 estimates"
    python -m advisor.sentiment --batch "text one" "text two" "text three"
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

# Windows-friendly Hugging Face cache location (must be set BEFORE importing transformers).
os.environ.setdefault("HF_HOME", str(Path.home() / ".cache" / "huggingface"))

try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except Exception:
    pass


MODEL_NAME = "ProsusAI/finbert"
MAX_TOKENS = 512  # BERT context window; longer text is truncated
LABELS = {"positive", "negative", "neutral"}


class FinBertScorer:
    """FinBERT-based sentiment scorer with lazy model loading and batching."""

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._tokenizer = None
        self._model = None
        self._device = None
        self._load_error: Optional[str] = None

    # ------------------------------------------------------------------ #
    def _ensure_loaded(self) -> bool:
        """Lazy-load the tokenizer + model. Returns False on failure."""
        if self._model is not None:
            return True
        if self._load_error is not None:
            return False
        try:
            print(f"[FinBertScorer] Downloading FinBERT (~440MB) on first use... "
                  f"cache={os.environ.get('HF_HOME')}", file=sys.stderr, flush=True)
            import torch
            from transformers import AutoTokenizer, AutoModelForSequenceClassification

            self._device = "cuda" if torch.cuda.is_available() else "cpu"
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
            self._model.to(self._device)
            self._model.eval()
            print(f"[FinBertScorer] Model loaded on {self._device}", file=sys.stderr, flush=True)
            return True
        except Exception as e:
            self._load_error = f"{type(e).__name__}: {e}"
            print(f"[FinBertScorer] Model load failed: {self._load_error}", file=sys.stderr)
            return False

    # ------------------------------------------------------------------ #
    @staticmethod
    def _neutral_result(error: Optional[str] = None) -> dict:
        out = {"label": "neutral", "score": 0.0, "confidence": 0.0}
        if error:
            out["error"] = error
        return out

    def _softmax_to_result(self, probs) -> dict:
        """Convert a length-3 tensor of probabilities to our result dict.

        FinBERT label order (from the model config) is positive, negative, neutral.
        """
        # Read from model.config to be robust against reordering
        id2label = {int(k): str(v).lower() for k, v in self._model.config.id2label.items()}
        best_id = int(probs.argmax().item())
        best_label = id2label.get(best_id, "neutral")
        conf = float(probs[best_id].item())
        if best_label == "positive":
            score = +conf
        elif best_label == "negative":
            score = -conf
        else:
            best_label = "neutral"
            score = 0.0
        return {"label": best_label, "score": round(score, 4),
                "confidence": round(conf, 4)}

    # ------------------------------------------------------------------ #
    def score(self, text: str) -> dict:
        """Score a single text; returns {label, score, confidence[, error]}."""
        if not text or not text.strip():
            return self._neutral_result()
        if not self._ensure_loaded():
            return self._neutral_result(error=self._load_error)
        try:
            import torch
            enc = self._tokenizer(
                text, return_tensors="pt",
                truncation=True, max_length=MAX_TOKENS, padding=False,
            ).to(self._device)
            with torch.no_grad():
                logits = self._model(**enc).logits[0]
            probs = torch.softmax(logits, dim=-1)
            return self._softmax_to_result(probs)
        except Exception as e:
            return self._neutral_result(error=f"{type(e).__name__}: {e}")

    def score_batch(self, texts: list[str]) -> list[dict]:
        """Batched inference. Empty entries return neutral."""
        if not texts:
            return []
        if not self._ensure_loaded():
            return [self._neutral_result(error=self._load_error) for _ in texts]
        try:
            import torch
            # Split into non-empty / empty; run only non-empty through the model.
            keep_idx = [i for i, t in enumerate(texts) if t and t.strip()]
            if not keep_idx:
                return [self._neutral_result() for _ in texts]
            batch_texts = [texts[i] for i in keep_idx]
            enc = self._tokenizer(
                batch_texts, return_tensors="pt",
                truncation=True, max_length=MAX_TOKENS, padding=True,
            ).to(self._device)
            with torch.no_grad():
                logits = self._model(**enc).logits
            probs = torch.softmax(logits, dim=-1)
            out: list[dict] = [self._neutral_result() for _ in texts]
            for slot, i in enumerate(keep_idx):
                out[i] = self._softmax_to_result(probs[slot])
            return out
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            return [self._neutral_result(error=err) for _ in texts]


# =========================================================================== #
#  Singleton
# =========================================================================== #
_scorer: Optional[FinBertScorer] = None


def get_scorer() -> FinBertScorer:
    global _scorer
    if _scorer is None:
        _scorer = FinBertScorer()
    return _scorer


# =========================================================================== #
#  CLI
# =========================================================================== #
def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Score financial text with FinBERT.")
    ap.add_argument("text", nargs="+", help="One or more texts to score.")
    ap.add_argument("--batch", action="store_true",
                    help="Score all texts in a single batch and print JSON list.")
    args = ap.parse_args(argv)

    scorer = get_scorer()
    if args.batch or len(args.text) > 1:
        results = scorer.score_batch(args.text)
        print(json.dumps([{"text": t[:120], **r}
                          for t, r in zip(args.text, results)], indent=2))
    else:
        r = scorer.score(args.text[0])
        print(json.dumps(r, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
