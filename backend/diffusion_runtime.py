from __future__ import annotations

import base64
import io
import os
import threading
import time
from dataclasses import dataclass

import torch
from diffusers import DiffusionPipeline


@dataclass
class DiffusionState:
    prompt: str
    latents: torch.Tensor
    prompt_embeds: torch.Tensor
    negative_prompt_embeds: torch.Tensor
    timesteps: torch.Tensor
    step_index: int = 0


class TinySDRuntime:
    """A local, stateful denoising runtime.

    Unlike pipeline(...).images[0], this keeps the latent and scheduler
    timestep between requests. `advance` performs exactly one scheduler step.
    """

    def __init__(self, model_id: str | None = None) -> None:
        self.model_id = model_id or os.getenv("DIFFUSION_MODEL", "segmind/tiny-sd")
        self.device = "mps" if torch.backends.mps.is_available() else "cpu"
        self.dtype = torch.float16 if self.device == "mps" else torch.float32
        self._pipe = None
        self._lock = threading.Lock()

    def _pipeline(self):
        if self._pipe is None:
            self._pipe = DiffusionPipeline.from_pretrained(self.model_id, torch_dtype=self.dtype)
            self._pipe = self._pipe.to(self.device)
            self._pipe.set_progress_bar_config(disable=True)
        return self._pipe

    def start(self, prompt: str, seed: int, steps: int = 8, guidance_scale: float = 7.5) -> DiffusionState:
        del guidance_scale  # guidance is applied in advance; kept in the public contract.
        with self._lock:
            pipe = self._pipeline()
            do_cfg = True
            positive, negative = pipe.encode_prompt(
                prompt=prompt,
                device=self.device,
                num_images_per_prompt=1,
                do_classifier_free_guidance=do_cfg,
            )[:2]
            height = pipe.unet.config.sample_size * pipe.vae_scale_factor
            width = height
            generator = torch.Generator(device="cpu").manual_seed(seed)
            latents = pipe.prepare_latents(
                1, pipe.unet.config.in_channels, height, width,
                self.dtype, self.device, generator,
            )
            pipe.scheduler.set_timesteps(steps, device=self.device)
            return DiffusionState(prompt, latents, positive, negative, pipe.scheduler.timesteps.detach().clone())

    def _preview(self, pipe, latents: torch.Tensor) -> str:
        with torch.no_grad():
            decoded = pipe.vae.decode(latents / pipe.vae.config.scaling_factor, return_dict=False)[0]
        image = ((decoded / 2 + 0.5).clamp(0, 1) * 255).byte()[0].permute(1, 2, 0).cpu().numpy()
        from PIL import Image
        buffer = io.BytesIO()
        Image.fromarray(image).save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    def advance(self, state: DiffusionState, rejection_mask: list[list[float]] | None = None, rejection_strength: float = 0.0, exploration_strength: float = 0.04) -> tuple[str, int, int]:
        started = time.perf_counter()
        with self._lock:
            pipe = self._pipeline()
            if state.step_index >= len(state.timesteps):
                # Explore never terminates at the terminal preview. Re-open
                # the scheduler from the retained latent and perturb it by a
                # low global amount (or a stronger local brush amount).
                if rejection_mask and rejection_strength > 0:
                    mask = torch.zeros((1, 1, state.latents.shape[-2], state.latents.shape[-1]), device=state.latents.device, dtype=state.latents.dtype)
                    for point in rejection_mask:
                        if len(point) >= 2:
                            x = min(max(int(float(point[0]) / 100 * mask.shape[-1]), 0), mask.shape[-1] - 1)
                            y = min(max(int(float(point[1]) / 100 * mask.shape[-2]), 0), mask.shape[-2] - 1)
                            mask[:, :, max(0, y - 2):min(mask.shape[-2], y + 3), max(0, x - 2):min(mask.shape[-1], x + 3)] = 1
                    # Re-noise with the scheduler so the latent remains in
                    # the model's expected scale; replacing it with raw noise
                    # produces near-black previews after intervention.
                    restart_noise = torch.randn_like(state.latents)
                    # Re-open near the current terminal state, not from the
                    # high-noise initial timestep the user already explored.
                    restart_index = max(len(state.timesteps) - 2, 0)
                    renoised = pipe.scheduler.add_noise(state.latents, restart_noise, state.timesteps[restart_index].reshape(1))
                    alpha = min(float(rejection_strength), 1.0)
                    state.latents = state.latents * (1 - mask * alpha) + renoised * (mask * alpha)
                else:
                    restart_noise = torch.randn_like(state.latents)
                    restart_index = max(len(state.timesteps) - 2, 0)
                    state.latents = pipe.scheduler.add_noise(state.latents, restart_noise, state.timesteps[restart_index].reshape(1))
                pipe.scheduler.set_timesteps(len(state.timesteps), device=self.device)
                state.timesteps = pipe.scheduler.timesteps.detach().clone()
                state.step_index = restart_index
            timestep = state.timesteps[state.step_index]
            latent_input = torch.cat([state.latents] * 2)
            latent_input = pipe.scheduler.scale_model_input(latent_input, timestep)
            embeds = torch.cat([state.negative_prompt_embeds, state.prompt_embeds])
            with torch.no_grad():
                noise = pipe.unet(latent_input, timestep, encoder_hidden_states=embeds, return_dict=False)[0]
            uncond, text = noise.chunk(2)
            noise = uncond + 7.5 * (text - uncond)
            state.latents = pipe.scheduler.step(noise, timestep, state.latents, return_dict=False)[0]
            if rejection_mask and rejection_strength > 0:
                mask = torch.zeros((1, 1, state.latents.shape[-2], state.latents.shape[-1]), device=state.latents.device, dtype=state.latents.dtype)
                for point in rejection_mask:
                    if len(point) >= 2:
                        x = min(max(int(float(point[0]) / 100 * mask.shape[-1]), 0), mask.shape[-1] - 1)
                        y = min(max(int(float(point[1]) / 100 * mask.shape[-2]), 0), mask.shape[-2] - 1)
                        mask[:, :, max(0, y - 2):min(mask.shape[-2], y + 3), max(0, x - 2):min(mask.shape[-1], x + 3)] = 1
                # Keep an intervention local and bounded while preserving the
                # surrounding latent solution.
                state.latents = state.latents + torch.randn_like(state.latents) * min(float(rejection_strength), 1.0) * 0.15 * mask
            # A malformed/overstrong intervention must not poison the VAE
            # decode and turn the entire preview black.
            state.latents = torch.nan_to_num(state.latents, nan=0.0, posinf=4.0, neginf=-4.0).clamp(-4.0, 4.0)
            state.step_index += 1
            return self._preview(pipe, state.latents), round((time.perf_counter() - started) * 1000), state.step_index
