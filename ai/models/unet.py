from __future__ import annotations

import torch
import torch.nn as nn


class DoubleConv(nn.Module):
    def __init__(self, in_ch: int, out_ch: int):
        super().__init__()
        self.net = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(out_ch, out_ch, 3, padding=1, bias=False),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


class UNetSmall(nn.Module):
    """Small UNet for 256x256 grayscale segmentation (demo-friendly)."""

    def __init__(self, in_channels: int = 1, out_channels: int = 1, features: list[int] | None = None):
        super().__init__()
        feats = features or [32, 64, 128, 256]

        self.downs = nn.ModuleList()
        self.pools = nn.ModuleList()
        ch = in_channels
        for f in feats:
            self.downs.append(DoubleConv(ch, f))
            self.pools.append(nn.MaxPool2d(2))
            ch = f

        self.bottleneck = DoubleConv(feats[-1], feats[-1] * 2)

        self.ups = nn.ModuleList()
        self.upconvs = nn.ModuleList()
        rev = list(reversed(feats))
        ch = feats[-1] * 2
        for f in rev:
            self.upconvs.append(nn.ConvTranspose2d(ch, f, kernel_size=2, stride=2))
            self.ups.append(DoubleConv(ch, f))
            ch = f

        self.head = nn.Conv2d(feats[0], out_channels, kernel_size=1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        skips: list[torch.Tensor] = []
        for down, pool in zip(self.downs, self.pools):
            x = down(x)
            skips.append(x)
            x = pool(x)

        x = self.bottleneck(x)

        skips = list(reversed(skips))
        for upconv, up, skip in zip(self.upconvs, self.ups, skips):
            x = upconv(x)
            if x.shape[-2:] != skip.shape[-2:]:
                x = torch.nn.functional.interpolate(x, size=skip.shape[-2:], mode="bilinear", align_corners=False)
            x = torch.cat([skip, x], dim=1)
            x = up(x)

        return self.head(x)

