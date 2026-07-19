import torch
import math
from torch.utils.data import Dataset, DataLoader
import h5py
import numpy as np
from pathlib import Path

class GeomagneticCosmicDataset(Dataset):
    """
    ScalogramV3 Dataset: Tensors + [Kp, Dst] Cosmic Features.
    Dioptimalkan: Membuka HDF5 sekali di __init__ untuk mencegah I/O Bottleneck.
    """
    def __init__(self, h5_file_path, group_name='train', transform=None, use_polarization=True, use_mad_norm=True, quantile=0.995):
        self.h5_file_path = str(h5_file_path)
        self.group_name = group_name
        self.transform = transform
        self.use_polarization = use_polarization
        self.use_mad_norm = use_mad_norm
        self.quantile = quantile
        
        try:
            # FIX 2: Membuka file untuk cek dimensi saja, tidak disimpan di memori
            with h5py.File(self.h5_file_path, 'r') as hf:
                if self.group_name not in hf:
                    raise KeyError(f"Grup {self.group_name} tidak ditemukan di HDF5")
                self.length = hf[self.group_name]['tensors'].shape[0]
            print(f"[OK] HDF5 Registered: {self.group_name} -> {self.length} samples.")
        except Exception as e:
            print(f"Error HDF5: {e}")
            self.length = 0

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        # FIX 1 (ANTI-LEAK): Buka dan tutup file secara langsung untuk tiap pemanggilan
        with h5py.File(self.h5_file_path, 'r', rdcc_nbytes=0) as hf:
            grp = hf[self.group_name]
            x_img    = np.array(grp['tensors'][idx], copy=True)
            x_cosmic = np.array(grp['cosmic_features'][idx], copy=True)
            y_event  = int(grp['label_event'][idx])
            y_mag    = float(grp['label_mag'][idx])
            y_azm    = float(grp['label_azm'][idx])
            # Convert degree azimuth to radian then sin/cos unit vector
            theta_rad = math.radians(y_azm)
            sin_theta = math.sin(theta_rad)
            cos_theta = math.cos(theta_rad)
            # Ensure unit norm (protect FP16)
            az_vec = torch.tensor([sin_theta, cos_theta], dtype=torch.float32)
            az_vec = torch.nn.functional.normalize(az_vec + 1e-6, dim=0)
            y_azm = az_vec
        
        # Konversi ke Tensor
        x_img    = torch.from_numpy(x_img).float()
        
        # Polarization feature engineering
        if self.use_polarization and x_img.shape[0] >= 3:
            # Use utilities for robust computation
            from utils.polarization import compute_polarization, mad_norm
            h_chan = x_img[0]
            z_chan = x_img[2]
            # Compute stacked tensor [H, Z, log1p(ratio)] with adaptive clipping
            x_img = compute_polarization(h_chan, z_chan, eps=1e-6, quantile=self.quantile)
            # Optional MAD normalization per channel
            if self.use_mad_norm:
                x_img = mad_norm(x_img)
        
        x_cosmic = torch.from_numpy(x_cosmic).float()
        
        # FIX 3: BOUNDED NORMALIZATION (Tanh) untuk mencegah exploding gradients
        # Kp Index: 0-9 -> bagi 9 agar terkunci di [0, 1]
        kp_norm  = x_cosmic[0] / 9.0
        
        # Dst Index: Normal ~0, badai bisa -300nT.
        # tanh(Dst/50) membatasi output di [-1, 1] secara elegan tanpa ledakan gradien
        dst_norm = torch.tanh(x_cosmic[1] / 50.0)
        
        # --- 🌪️ [NEW] SYNTHETIC STORM INJECTION (CALIBRATION FIX) ---
        # Mengurangi 'Trauma' model dari 15% ke 2% sesuai instruksi
        if y_event == 0 and torch.rand(1).item() < 0.02:
            kp_norm = torch.tensor(1.0)  # Forced Storm (Kp=9)
            dst_norm = torch.tensor(-1.0) # Forced Storm (Dst peak)
            
        x_cosmic_safe = torch.stack([kp_norm, dst_norm]).float()
        
        if self.transform:
            x_img = self.transform(x_img)
            
        return x_img, x_cosmic_safe, y_event, y_mag, y_azm
    
    def __del__(self):
        pass

def create_v3_dataloaders(h5_path, batch_size=16, num_workers=0, use_sampler=True, use_polarization=True, use_mad_norm=True, quantile=0.995):
    train_dataset = GeomagneticCosmicDataset(h5_path, group_name='train', use_polarization=use_polarization, use_mad_norm=use_mad_norm, quantile=quantile)
    val_dataset   = GeomagneticCosmicDataset(h5_path, group_name='val', use_polarization=use_polarization, use_mad_norm=use_mad_norm, quantile=quantile)
    
    sampler = None
    shuffle = True
    
    if use_sampler:
        # Hitung bobot sampel untuk menangani imbalance 1:10
        # Baca label dari dataset internal (group 'train')
        with h5py.File(h5_path, 'r') as hf:
            labels = hf['train/label_event'][:]
            
        class_counts = np.bincount(labels) # [count0, count1]
        class_weights = 1. / torch.tensor(class_counts, dtype=torch.float)
        sample_weights = class_weights[labels]
        
        sampler = torch.utils.data.WeightedRandomSampler(
            weights=sample_weights, 
            num_samples=len(sample_weights), 
            replacement=True
        )
        shuffle = False # Sampler handle shuffle
        print(f"[OK] WeightedRandomSampler Active (Class Counts: {class_counts})")

    # num_workers=0 wajib karena HDF5 dibuka sekali di RAM (tidak thread-safe)
    train_loader = DataLoader(
        train_dataset, batch_size=batch_size, shuffle=shuffle, sampler=sampler,
        num_workers=num_workers, pin_memory=False, drop_last=True
    )
    val_loader = DataLoader(
        val_dataset, batch_size=batch_size, shuffle=False,
        num_workers=num_workers, pin_memory=False
    )
    return train_loader, val_loader

if __name__ == '__main__':
    h5_v3 = r"d:\multi\scalogramv3\scalogram_v3_augmented.h5"
    if Path(h5_v3).exists():
        ds = GeomagneticCosmicDataset(h5_v3, group_name='train')
        if len(ds) > 0:
            img, cos, ev, mag, azm = ds[0]
            print("\n--- Smoke Test DataLoader V3 ---")
            print(f"Img Shape     : {img.shape}")
            print(f"Cosmic Vector : {cos} [Kp_norm, Dst_tanh]")
            print(f"Labels        : Event={ev}, Mag={mag}, Azm={azm}")
    else:
        print("HDF5 V3 belum siap.")
