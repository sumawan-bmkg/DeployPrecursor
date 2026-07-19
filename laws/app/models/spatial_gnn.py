#!/usr/bin/env python3
"""
SpatialGNNModule — Standalone GAT for LAWS operational deployment.
Reconstructed for checkpoint compatibility (submodule naming: gat1.W, gat1.a, gat1.norm).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class _GATLayer(nn.Module):
    """Single GAT layer with submodule naming for checkpoint compatibility."""
    def __init__(self, in_features, out_features, n_heads):
        super().__init__()
        self.W = nn.Linear(in_features, out_features, bias=False)
        self.a = nn.Parameter(torch.randn(n_heads, 2 * (out_features // n_heads)))
        self.norm = nn.LayerNorm(out_features)

    def forward(self, x, return_attention=False):
        B, N, D = x.shape
        out_feat = self.W.out_features
        n_heads = self.a.shape[0]
        d_head = out_feat // n_heads

        h = self.W(x)  # (B, N, out_feat)

        # Multi-head attention
        x_heads = h.view(B, N, n_heads, d_head)
        x_heads_t = x_heads.transpose(1, 2)  # (B, n_heads, N, d_head)

        att_scores = []
        for i in range(n_heads):
            a_i = self.a[i]
            a_left = a_i[:d_head].view(1, d_head)
            a_right = a_i[d_head:].view(1, d_head)
            x_i = x_heads_t[:, i]  # (B, N, d_head)
            left = torch.matmul(x_i, a_left.t())   # (B, N, 1)
            right = torch.matmul(x_i, a_right.t())  # (B, N, 1)
            att = left + right.transpose(1, 2)       # (B, N, N)
            att_scores.append(att)

        att_scores = torch.stack(att_scores, dim=1)  # (B, n_heads, N, N)
        att_scores = F.leaky_relu(att_scores, negative_slope=0.2)
        att_weights = F.softmax(att_scores, dim=3)

        out = torch.matmul(att_weights, x_heads_t)  # (B, n_heads, N, d_head)
        out = out.transpose(1, 2).contiguous().view(B, N, out_feat)
        out = self.norm(out)

        if return_attention:
            avg_att = att_weights.mean(dim=1).mean(dim=2)
            return out, avg_att
        return out


class _ConsensusHead(nn.Module):
    """Wrapper to hold k_sensitivity as a registered parameter under 'consensus' name."""
    def __init__(self):
        super().__init__()
        self.k_sensitivity = nn.Parameter(torch.tensor(1.0))


class SpatialGNNModule(nn.Module):
    """2-layer Graph Attention Network with submodule naming (V4 compatible)."""
    def __init__(self, in_features=512, hidden=256, out_features=512, n_heads=4):
        super().__init__()
        self.in_features, self.hidden = in_features, hidden
        self.out_features, self.n_heads = out_features, n_heads

        self.gat1 = _GATLayer(in_features, hidden, n_heads)
        self.gat2 = _GATLayer(hidden, out_features, n_heads)
        self.consensus = _ConsensusHead()

        self._init_weights()

    def _init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.Linear):
                nn.init.xavier_uniform_(m.weight)
        for name, p in self.named_parameters():
            if name.endswith('.a'):
                nn.init.normal_(p, mean=0.0, std=0.1)

    def forward(self, station_features, station_probs):
        B, N, D = station_features.shape

        h1 = self.gat1(station_features)
        h2, att_weights = self.gat2(h1, return_attention=True)

        consensus_feat = h2.mean(dim=1)
        reg_score = torch.sigmoid(consensus_feat.max(dim=1, keepdim=True)[0])
        th = self.consensus.k_sensitivity * station_probs.std(dim=1, keepdim=True).mean()

        return consensus_feat, reg_score, th, att_weights
