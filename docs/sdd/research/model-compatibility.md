# Real model compatibility notes

This note records what is technically compatible with the Stateful Diffusion
Runtime contract. It is not a claim that the model has already been installed
or benchmarked locally.

## Current local evidence

- `segmind/tiny-sd`: present in the local Hugging Face cache and exercised by
  `backend/diffusion_runtime.py` on Apple MPS.
- SD 1.5, SDXL, ControlNet, and LCM: not present in the local cache at the
  time of this check, so they are candidates, not verified backends.

## Compatibility matrix

| Candidate | Stateful latent loop | Guide Canvas conditioning | Noise Brush | Practical next step |
|---|---:|---|---|---|
| TinySD | Yes, current implementation | Weak spatial latent bias | Local re-noising | Keep as v0.1 reference runtime |
| Stable Diffusion 1.5 | Yes, likely lowest-risk replacement | ControlNet or adapter for strong guide control | Local re-noising / SDEdit-style step | Add model-configurable pipeline and run a real regression |
| SDXL base | Yes in principle, but larger and slower | SDXL ControlNet or T2I-Adapter | Local re-noising, with more memory pressure | Separate backend profile; do not silently swap into TinySD |
| SDXL base + refiner | Base can be stateful; refiner is a separate stage | Conditioning belongs to the base stage | Brush should affect base latent before refining | Defer until base runtime is stable |
| ControlNet (SD 1.5/SDXL) | Yes through the underlying Diffusers pipeline | Strong spatial guide conditioning | Compatible with the same rejection mask contract | v0.2/v0.3 adapter, not required for v0.1 |
| LCM / LCM-LoRA | Yes, but only with a compatible scheduler/model setup | Depends on the base model and adapter | Compatible, but few-step dynamics need retuning | Optional fast runtime profile after baseline |
| ComfyUI adapter | Depends on workflow; not guaranteed stateful | Can expose ControlNet and other nodes | Requires a custom state/session strategy | Spike only; preserve this UI and contract |

## Decision

The next real-model experiment should be Stable Diffusion 1.5, not SDXL. It
has the closest architecture to the current TinySD code path and is more
realistic on the current Apple MPS setup. SDXL is feasible through Diffusers,
but its second text encoder, larger UNet, higher recommended resolution, and
memory cost make it a separate runtime profile rather than a drop-in model
name.

ControlNet is the proper way to make a drawn Guide Canvas semantically guide
the image. The current TinySD guide implementation is deliberately only a
weak latent bias because TinySD does not provide a ControlNet path in this
prototype. LCM is a scheduler/runtime optimization, not a replacement for
the stateful session contract.

## Verification rule

A candidate is not considered supported until it passes the same regression
scenarios as TinySD: prompt difference, guide difference, brush difference,
continued exploration, non-black previews, and snapshot restore equality.

