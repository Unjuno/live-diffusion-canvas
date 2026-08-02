# Real model compatibility notes

This note records what is technically compatible with the Stateful Diffusion
Runtime contract. It is not a claim that the model has already been installed
or benchmarked locally.

## Current local evidence

- `segmind/tiny-sd`: present in the local Hugging Face cache and exercised by
  `backend/diffusion_runtime.py` on Apple MPS.
- `stable-diffusion-v1-5/stable-diffusion-v1-5`: downloaded into the local
  cache and verified through the real FastAPI runtime on Apple MPS. One
  stateful preview request completed successfully at 512x512.
- `stabilityai/sdxl-turbo`: downloaded into the local cache and verified
  through the real FastAPI runtime on Apple MPS with the 16-frame midstream
  intervention regression. The SDXL VAE is decoded in float32 to avoid the
  black-preview failure observed with fp16 decoding.
- `stabilityai/sd-turbo`: downloaded through the background worker and
  verified on Apple MPS with the 16-frame intervention regression and
  Snapshot/Restore/Finish. It uses guidance=1 internally because it is
  guidance-distilled.
- `stabilityai/stable-diffusion-xl-base-1.0`: downloaded through the
  background worker and verified on Apple MPS with the 16-frame intervention
  regression and Snapshot/Restore/Finish.
- `black-forest-labs/FLUX.1-schnell`: dedicated Transformer runtime adapter is
  implemented, but the Hub repository is gated and returned HTTP 403 here.
- `stabilityai/stable-diffusion-3.5-medium`: dedicated Transformer runtime
  adapter is implemented, but the Hub repository is gated and returned HTTP
  403 here.

## Compatibility matrix

| Model | Basic generation | Stateful loop | Guide Canvas | Noise Brush | Snapshot | Status |
|---|---:|---:|---:|---:|---:|---|
| TinySD | Yes | Yes | Yes, weak latent bias | Yes | Yes | Verified |
| Stable Diffusion 1.5 | Yes | Yes | Yes, weak latent bias | Yes | Yes | Verified on Apple MPS |
| SD-Turbo | Yes | Yes | Yes, weak latent bias | Yes | Yes | Verified on Apple MPS |
| SDXL-Turbo | Yes | Yes | Yes, weak latent bias | Yes | Yes | Verified on Apple MPS |
| SDXL base | Yes | Yes | Yes, weak latent bias | Yes | Yes | Verified on Apple MPS |
| FLUX.1 schnell/dev | Adapter ready; weights gated | Pending | Pending | Pending | Pending | HF authorization required |
| Stable Diffusion 3.5 Medium | Adapter ready; weights gated | Pending | Pending | Pending | Pending | HF authorization required |

“Verified” means the same runtime contract was exercised: generated frames
changed, one session continued across intervention, Guide Canvas and Noise
Brush changed the output, previews did not go black, and Snapshot restore/Finish
remained available. A model being listed in the selector does not imply this
level of support.
| SDXL base + refiner | Base can be stateful; refiner is a separate stage | Conditioning belongs to the base stage | Brush should affect base latent before refining | Defer until base runtime is stable |
| ControlNet (SD 1.5/SDXL) | Yes through the underlying Diffusers pipeline | Strong spatial guide conditioning | Compatible with the same rejection mask contract | v0.2/v0.3 adapter, not required for v0.1 |
| LCM / LCM-LoRA | Yes, but only with a compatible scheduler/model setup | Depends on the base model and adapter | Compatible, but few-step dynamics need retuning | Optional fast runtime profile after baseline |
| ComfyUI adapter | Depends on workflow; not guaranteed stateful | Can expose ControlNet and other nodes | Requires a custom state/session strategy | Spike only; preserve this UI and contract |
| FLUX.1 | Requires a dedicated FluxPipeline runtime | Requires FLUX-specific conditioning work | Requires a FLUX latent intervention design | Dedicated backend profile; do not route through the SD runtime |

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

A candidate is not considered verified until it passes the same regression
scenarios as TinySD. Gated candidates are not marked verified merely because
their adapter imports successfully.
