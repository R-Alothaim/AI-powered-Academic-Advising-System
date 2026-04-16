"""Tests for distillation loss."""

import torch

from advisor.distillation.losses import distillation_loss


def test_loss_returns_scalar_and_dict():
    B, T, V = 2, 10, 100
    student = torch.randn(B, T, V)
    teacher = torch.randn(B, T, V)
    labels = torch.randint(0, V, (B, T))

    loss, d = distillation_loss(student, teacher, labels)

    assert loss.shape == ()
    assert loss.requires_grad
    assert "loss_ce" in d
    assert "loss_kd" in d
    assert "loss_total" in d


def test_identical_logits_low_kd_loss():
    B, T, V = 2, 10, 50
    logits = torch.randn(B, T, V)
    labels = torch.randint(0, V, (B, T))

    _, d = distillation_loss(logits, logits.clone(), labels, temperature=4.0)

    assert d["loss_kd"] < 0.01


def test_alpha_weighting():
    B, T, V = 2, 10, 50
    student = torch.randn(B, T, V)
    teacher = torch.randn(B, T, V)
    labels = torch.randint(0, V, (B, T))

    _, d_ce = distillation_loss(student, teacher, labels, alpha_ce=1.0, alpha_kd=0.0)
    _, d_kd = distillation_loss(student, teacher, labels, alpha_ce=0.0, alpha_kd=1.0)

    # With alpha_kd=0, total should equal CE; with alpha_ce=0, should not
    assert abs(d_ce["loss_total"] - d_ce["loss_ce"]) < 1e-4
    assert abs(d_kd["loss_total"] - d_kd["loss_kd"]) < 1e-4


def test_ignore_index_respected():
    B, T, V = 1, 5, 20
    student = torch.randn(B, T, V)
    teacher = torch.randn(B, T, V)
    labels = torch.full((B, T), -100)  # all masked

    _, d = distillation_loss(student, teacher, labels)

    assert d["loss_ce"] == 0.0
