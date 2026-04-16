"""Knowledge distillation loss functions.

Combines the standard cross-entropy on hard labels with KL-divergence
between the student and teacher soft-label distributions.
"""

from __future__ import annotations

import torch
import torch.nn.functional as F
from torch import Tensor


def distillation_loss(
    student_logits: Tensor,
    teacher_logits: Tensor,
    labels: Tensor,
    temperature: float = 4.0,
    alpha_ce: float = 0.5,
    alpha_kd: float = 0.5,
    label_smoothing: float = 0.0,
    ignore_index: int = -100,
) -> tuple[Tensor, dict[str, float]]:
    """Compute the combined knowledge-distillation loss.

    L = alpha_ce * CE(student, labels) + alpha_kd * T^2 * KL(student_soft || teacher_soft)

    Returns:
        (loss, {"loss_ce": ..., "loss_kd": ..., "loss_total": ...})
    """
    # Hard-label cross-entropy
    loss_ce = F.cross_entropy(
        student_logits.view(-1, student_logits.size(-1)),
        labels.view(-1),
        ignore_index=ignore_index,
        label_smoothing=label_smoothing,
    )

    # Soft-label KL divergence
    student_soft = F.log_softmax(student_logits / temperature, dim=-1)
    teacher_soft = F.softmax(teacher_logits / temperature, dim=-1)

    # Mask out positions we should ignore
    mask = (labels != ignore_index).unsqueeze(-1).float()
    student_soft = student_soft * mask
    teacher_soft = teacher_soft * mask

    loss_kd = F.kl_div(
        student_soft.view(-1, student_soft.size(-1)),
        teacher_soft.view(-1, teacher_soft.size(-1)),
        reduction="batchmean",
        log_target=False,
    ) * (temperature ** 2)

    loss = alpha_ce * loss_ce + alpha_kd * loss_kd

    return loss, {
        "loss_ce": loss_ce.item(),
        "loss_kd": loss_kd.item(),
        "loss_total": loss.item(),
    }
