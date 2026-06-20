import sys
import os
import torch

sys.path.append(f"{os.getcwd()}/GPT_SoVITS/eres2net")

# Lazy-load SV model (pretrained_eres2netv2 ckpt may be in weights_dir)
_sv_model = None

def _resolve_sv_path():
    """Finds the SV pretrained ckpt from sovits_root or SOVITS_WEIGHTS_DIR."""
    candidates = [
        os.path.join(os.getcwd(), "GPT_SoVITS", "pretrained_models", "sv",
                     "pretrained_eres2netv2w24s4ep4.ckpt"),
    ]
    weights_dir = os.environ.get("SOVITS_WEIGHTS_DIR", "")
    if weights_dir:
        candidates.insert(0, os.path.join(weights_dir, "GPT_SoVITS",
                         "pretrained_models", "sv",
                         "pretrained_eres2netv2w24s4ep4.ckpt"))
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]  # fallback (will fail with clear error)


class SV:
    def __init__(self, device, is_half):
        sv_path = _resolve_sv_path()
        pretrained_state = torch.load(sv_path, map_location="cpu", weights_only=False)
        from ERes2NetV2 import ERes2NetV2
        embedding_model = ERes2NetV2(baseWidth=24, scale=4, expansion=4)
        embedding_model.load_state_dict(pretrained_state)
        embedding_model.eval()
        self.embedding_model = embedding_model
        if is_half == False:
            self.embedding_model = self.embedding_model.to(device)
        else:
            self.embedding_model = self.embedding_model.half().to(device)
        self.is_half = is_half

    def compute_embedding3(self, wav):
        import kaldi as Kaldi
        with torch.no_grad():
            if self.is_half == True:
                wav = wav.half()
            feat = torch.stack(
                [Kaldi.fbank(wav0.unsqueeze(0), num_mel_bins=80, sample_frequency=16000, dither=0) for wav0 in wav]
            )
            sv_emb = self.embedding_model.forward3(feat)
        return sv_emb
