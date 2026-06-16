#!/usr/bin/env python3
"""
SpatialGNNModule - Graph Attention Network for Spatial Feature Aggregation

Reconstructed from checkpoint analysis of v3_v8_conv_fpr_best_weights.pth

Architecture:
- 2-layer Graph Attention Network (GAT)
- Multi-head attention (4 heads)
- LayerNorm after each GAT layer
- Consensus mechanism for regional scoring

Checkpoint Keys:
- gnn.gat1.a: [4, 128]
- gnn.gat1.W.weight: [256, 512]
- gnn.gat1.norm.weight: [256]
- gnn.gat1.norm.bias: [256]
- gnn.gat2.a: [4, 256]
- gnn.gat2.W.weight: [512, 256]
- gnn.gat2.norm.weight: [512]
- gnn.gat2.norm.bias: [512]
- gnn.consensus.k_sensitivity: []

Author: Reconstructed by Cascade AI
Date: 2026-06-10
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class SpatialGNNModule(nn.Module):
    """
    Spatial Graph Attention Network Module
    
    Aggregates features from 8 stations using Graph Attention Network (GAT)
    and computes consensus features, regional score, and dynamic threshold.
    
    Args:
        in_features: Input feature dimension (default: 512)
        hidden: Hidden dimension for GAT layer 1 (default: 256)
        out_features: Output feature dimension (default: 512)
        n_heads: Number of attention heads (default: 4)
    """
    
    def __init__(self, in_features=512, hidden=256, out_features=512, n_heads=4):
        super().__init__()
        
        self.in_features = in_features
        self.hidden = hidden
        self.out_features = out_features
        self.n_heads = n_heads
        
        # GAT Layer 1: in_features -> hidden
        self.gat1_W = nn.Linear(in_features, hidden, bias=False)
        self.gat1_a = nn.Parameter(torch.randn(n_heads, hidden // n_heads * 2))
        self.gat1_norm = nn.LayerNorm(hidden)
        
        # GAT Layer 2: hidden -> out_features
        self.gat2_W = nn.Linear(hidden, out_features, bias=False)
        self.gat2_a = nn.Parameter(torch.randn(n_heads, out_features // n_heads * 2))
        self.gat2_norm = nn.LayerNorm(out_features)
        
        # Consensus mechanism
        self.k_sensitivity = nn.Parameter(torch.tensor(1.0))
        
        self._init_weights()
    
    def _init_weights(self):
        """Initialize weights"""
        nn.init.xavier_uniform_(self.gat1_W.weight)
        nn.init.xavier_uniform_(self.gat2_W.weight)
        nn.init.normal_(self.gat1_a, mean=0.0, std=0.1)
        nn.init.normal_(self.gat2_a, mean=0.0, std=0.1)
    
    def forward(self, station_features, station_probs):
        """
        Forward pass
        
        Args:
            station_features: (B, 8, in_features) - features from 8 stations
            station_probs: (B, 8) - probability scores for each station
        
        Returns:
            consensus_feat: (B, out_features) - consensus features
            reg_score: (B, 1) - regional score
            th: scalar - dynamic threshold
            att_weights: (B, 8) - attention weights
        """
        B, N, D = station_features.shape  # N=8 stations
        
        # GAT Layer 1
        h1 = self.gat1_W(station_features)  # (B, 8, hidden)
        h1 = self.gat_layer(h1, self.gat1_a, self.n_heads)  # (B, 8, hidden)
        h1 = self.gat1_norm(h1)
        
        # GAT Layer 2
        h2 = self.gat2_W(h1)  # (B, 8, out_features)
        h2, att_weights = self.gat_layer(h2, self.gat2_a, self.n_heads, return_attention=True)
        h2 = self.gat2_norm(h2)  # (B, 8, out_features)
        
        # Consensus aggregation
        consensus_feat = h2.mean(dim=1)  # (B, out_features)
        
        # Regional score: max feature value passed through sigmoid
        reg_score = torch.sigmoid(consensus_feat.max(dim=1, keepdim=True)[0])  # (B, 1)
        
        # Dynamic threshold: based on station probability variance
        th = self.k_sensitivity * station_probs.std(dim=1, keepdim=True).mean()
        
        return consensus_feat, reg_score, th, att_weights
    
    def gat_layer(self, x, a, n_heads, return_attention=False):
        """
        Graph Attention Layer
        
        Args:
            x: (B, N, D) - node features
            a: (n_heads, 2*D/n_heads) - attention coefficients
            n_heads: number of attention heads
            return_attention: whether to return attention weights
        
        Returns:
            out: (B, N, D) - output features
            att_weights: (B, N) - attention weights (if return_attention)
        """
        B, N, D = x.shape
        d_head = D // n_heads
        
        # Split into heads
        x_heads = x.view(B, N, n_heads, d_head)  # (B, N, n_heads, d_head)
        
        # Compute attention scores
        # e_ij = a^T [x_i || x_j]
        # For efficiency, use matrix operations
        
        # Reshape for batch matrix multiplication
        # x_heads: (B, N, n_heads, d_head) -> (B*n_heads, N, d_head)
        x_heads_reshaped = x_heads.transpose(1, 2).contiguous().view(B * n_heads, N, d_head)
        
        # Compute pairwise attention using matrix operations
        # For each head, compute attention between all pairs of nodes
        att_scores_list = []
        
        for h in range(n_heads):
            x_h = x_heads_reshaped[h*B:(h+1)*B]  # (B, N, d_head)
            
            # Compute attention scores: a_h^T [x_i || x_j]
            # This is equivalent to: (x_h @ a_h_left) + (x_h @ a_h_right)
            a_h = a[h]  # (2*d_head)
            a_left = a_h[:d_head].view(1, d_head)  # (1, d_head)
            a_right = a_h[d_head:].view(1, d_head)  # (1, d_head)
            
            # Compute: x_i @ a_left + x_j @ a_right
            # Using broadcasting: (B, N, d_head) @ (d_head, 1) -> (B, N, 1)
            left = torch.matmul(x_h, a_left.t())  # (B, N, 1)
            right = torch.matmul(x_h, a_right.t())  # (B, N, 1)
            
            # Sum: (B, N, 1) + (B, 1, N) -> (B, N, N)
            att_scores_h = left + right.transpose(1, 2)  # (B, N, N)
            att_scores_list.append(att_scores_h)
        
        # Stack heads: (n_heads, B, N, N) -> (B, n_heads, N, N)
        att_scores = torch.stack(att_scores_list, dim=1)  # (B, n_heads, N, N)
        
        # Apply LeakyReLU
        att_scores = F.leaky_relu(att_scores, negative_slope=0.2)
        
        # Softmax across nodes (dim=3 is the j index)
        att_weights = F.softmax(att_scores, dim=3)  # (B, n_heads, N, N)
        
        # Aggregate features
        # Reshape for aggregation
        # x_heads: (B, N, n_heads, d_head) -> (B, n_heads, N, d_head)
        x_heads_transposed = x_heads.transpose(1, 2)  # (B, n_heads, N, d_head)
        
        # Weighted sum: (B, n_heads, N, N) @ (B, n_heads, N, d_head) -> (B, n_heads, N, d_head)
        agg = torch.matmul(att_weights, x_heads_transposed)  # (B, n_heads, N, d_head)
        
        # Concatenate heads: (B, n_heads, N, d_head) -> (B, N, n_heads, d_head) -> (B, N, D)
        out = agg.transpose(1, 2).contiguous().view(B, N, D)  # (B, N, D)
        
        # Average attention weights across heads and nodes
        # att_weights: (B, n_heads, N, N) -> mean over heads -> (B, N, N) -> mean over j -> (B, N)
        avg_att = att_weights.mean(dim=1).mean(dim=2)  # (B, N)
        
        if return_attention:
            return out, avg_att
        return out


# Smoke test
if __name__ == "__main__":
    print("Testing SpatialGNNModule...")
    
    # Initialize
    model = SpatialGNNModule(in_features=512, hidden=256, out_features=512, n_heads=4)
    
    # Test forward pass
    B = 2
    N = 8
    D = 512
    station_features = torch.randn(B, N, D)
    station_probs = torch.ones(B, N) * 0.5
    
    consensus, reg_score, th, att = model(station_features, station_probs)
    
    print(f"Input shapes:")
    print(f"  station_features: {station_features.shape}")
    print(f"  station_probs: {station_probs.shape}")
    print(f"\nOutput shapes:")
    print(f"  consensus_feat: {consensus.shape}")
    print(f"  reg_score: {reg_score.shape}")
    print(f"  th: {th.shape if hasattr(th, 'shape') else 'scalar'}")
    print(f"  att_weights: {att.shape}")
    
    # Verify shapes
    assert consensus.shape == (B, 512), f"Expected (B, 512), got {consensus.shape}"
    assert reg_score.shape == (B, 1), f"Expected (B, 1), got {reg_score.shape}"
    assert att.shape == (B, N), f"Expected (B, {N}), got {att.shape}"
    
    print("\n✅ All shape checks passed!")
    
    # Test checkpoint compatibility
    print("\nTesting checkpoint key compatibility...")
    state_dict = model.state_dict()
    expected_keys = [
        'gat1_W.weight',
        'gat1_a',
        'gat1_norm.weight',
        'gat1_norm.bias',
        'gat2_W.weight',
        'gat2_a',
        'gat2_norm.weight',
        'gat2_norm.bias',
        'k_sensitivity'
    ]
    
    for key in expected_keys:
        assert key in state_dict, f"Missing key: {key}"
    
    print(f"✅ All {len(expected_keys)} expected keys present!")
    
    # Print key shapes
    print("\nKey shapes:")
    for key in expected_keys:
        shape = state_dict[key].shape
        print(f"  {key}: {shape}")
    
    print("\n✅ SpatialGNNModule test PASSED!")
