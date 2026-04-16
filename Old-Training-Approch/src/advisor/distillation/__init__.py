__all__ = ["DistillationTrainer"]


def DistillationTrainer(*args, **kwargs):  # noqa: N802
    """Lazy import to avoid hard torch dependency at import time."""
    from advisor.distillation.trainer import DistillationTrainer as _Cls
    return _Cls(*args, **kwargs)
