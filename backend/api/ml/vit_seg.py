"""
Arquitectura ViT + Decoder para segmentación de pólipos.

IMPORTANTE: esta clase es estructuralmente idéntica a la usada en el
entrenamiento (pruebin.py / entrenamiento_vit_segmentacion_corregido.py)
para que el checkpoint my_vit_segmentation_model.pth cargue sin errores.
"""
import torch
import torch.nn as nn
import timm


class ViTSegmentation(nn.Module):
    """Encoder ViT-Base/16 preentrenado + decoder convolucional.

    Entrada : [B, 3, 224, 224]
    Salida  : [B, 1, 224, 224]  (logits; aplicar sigmoid + umbral 0.5)
    """

    def __init__(self, img_size=224, patch_size=16, embed_dim=768, out_channels=1):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.grid_size = img_size // patch_size  # 224 / 16 = 14

        # ENCODER: ViT preentrenado en ImageNet (sin descargar pesos: offline)
        self.encoder = timm.create_model("vit_base_patch16_224", pretrained=False)
        self.encoder.head = nn.Identity()

        # DECODER: 14x14 -> 28x28 -> 56x56 -> 112x112 -> 224x224
        self.decoder = nn.Sequential(
            nn.Conv2d(embed_dim, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(256, 128, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(128, 64, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(64, 32, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(inplace=True),
            nn.ConvTranspose2d(32, 16, kernel_size=4, stride=2, padding=1),
            nn.BatchNorm2d(16),
            nn.ReLU(inplace=True),
            nn.Conv2d(16, out_channels, kernel_size=1),
        )

    def forward(self, x):
        B = x.shape[0]

        features = self.encoder.forward_features(x)  # [B, 197, 768]
        if features.ndim != 3:
            raise RuntimeError(f"Salida inesperada de ViT: {features.shape}")

        patch_tokens = features[:, 1:, :]  # quitamos token [CLS] -> [B, 196, 768]

        expected = self.grid_size * self.grid_size
        if patch_tokens.shape[1] != expected:
            raise RuntimeError(
                "Tokens del ViT no coinciden con la cuadrícula esperada: "
                f"{patch_tokens.shape[1]} vs {expected}"
            )

        # [B, 196, 768] -> [B, 768, 14, 14]
        x_spatial = patch_tokens.transpose(1, 2).reshape(
            B, -1, self.grid_size, self.grid_size
        )

        return self.decoder(x_spatial)  # [B, 1, 224, 224]
