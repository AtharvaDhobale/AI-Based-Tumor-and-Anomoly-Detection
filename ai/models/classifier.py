from __future__ import annotations

import torch
import torch.nn as nn
from torchvision.models import resnet18, ResNet18_Weights


class ResNet18Classifier(nn.Module):
    """ResNet18 adapted for 1-channel MRI slices."""

    def __init__(self, num_classes: int = 2, pretrained: bool = True):
        super().__init__()
        weights = ResNet18_Weights.DEFAULT if pretrained else None
        backbone = resnet18(weights=weights)

        # Adapt first conv from 3->1 channels by averaging pretrained weights.
        old_conv = backbone.conv1
        backbone.conv1 = nn.Conv2d(1, old_conv.out_channels, kernel_size=old_conv.kernel_size, stride=old_conv.stride, padding=old_conv.padding, bias=False)
        if pretrained and weights is not None:
            with torch.no_grad():
                backbone.conv1.weight.copy_(old_conv.weight.mean(dim=1, keepdim=True))

        backbone.fc = nn.Linear(backbone.fc.in_features, num_classes)
        self.backbone = backbone

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)

