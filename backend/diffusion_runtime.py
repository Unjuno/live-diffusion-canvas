from __future__ import annotations

import base64
import io
import os
import re
from pathlib import Path
from urllib.parse import unquote
import threading
import time
from dataclasses import dataclass

import torch
from diffusers import DDIMScheduler, DiffusionPipeline, FluxPipeline, StableDiffusion3Pipeline
from diffusers.pipelines.flux.pipeline_flux import calculate_shift, retrieve_timesteps as flux_retrieve_timesteps
from diffusers.pipelines.stable_diffusion_3.pipeline_stable_diffusion_3 import retrieve_timesteps as sd3_retrieve_timesteps


@dataclass
class DiffusionState:
    prompt: str
    latents: torch.Tensor
    prompt_embeds: torch.Tensor
    negative_prompt_embeds: torch.Tensor
    timesteps: torch.Tensor
    added_cond_kwargs: dict[str, torch.Tensor] | None = None
    step_index: int = 0
    guide_mask: torch.Tensor | None = None
    guide_influence: float = 0.0
    guide_composite: str | None = None
    imported_image: str | None = None
    guide_erase_mask: str | None = None
    guidance_scale: float = 7.5
    requested_steps: int = 8
    exploration_cycle: int = 0
    pooled_prompt_embeds: torch.Tensor | None = None
    negative_pooled_prompt_embeds: torch.Tensor | None = None
    text_ids: torch.Tensor | None = None
    negative_text_ids: torch.Tensor | None = None
    latent_image_ids: torch.Tensor | None = None
    transformer_mode: str | None = None
    height: int = 512
    width: int = 512

    def clone(self) -> "DiffusionState":
        return DiffusionState(
            prompt=self.prompt,
            latents=self.latents.detach().clone(),
            prompt_embeds=self.prompt_embeds.detach().clone(),
            negative_prompt_embeds=self.negative_prompt_embeds.detach().clone(),
            added_cond_kwargs={key: value.detach().clone() for key, value in self.added_cond_kwargs.items()} if self.added_cond_kwargs else None,
            timesteps=self.timesteps.detach().clone(),
            step_index=self.step_index,
            guide_mask=self.guide_mask.detach().clone() if self.guide_mask is not None else None,
            guide_influence=self.guide_influence,
            guide_composite=self.guide_composite,
            imported_image=self.imported_image,
            guide_erase_mask=self.guide_erase_mask,
            guidance_scale=self.guidance_scale,
            requested_steps=self.requested_steps,
            exploration_cycle=self.exploration_cycle,
            pooled_prompt_embeds=self.pooled_prompt_embeds.detach().clone() if self.pooled_prompt_embeds is not None else None,
            negative_pooled_prompt_embeds=self.negative_pooled_prompt_embeds.detach().clone() if self.negative_pooled_prompt_embeds is not None else None,
            text_ids=self.text_ids.detach().clone() if self.text_ids is not None else None,
            negative_text_ids=self.negative_text_ids.detach().clone() if self.negative_text_ids is not None else None,
            latent_image_ids=self.latent_image_ids.detach().clone() if self.latent_image_ids is not None else None,
            transformer_mode=self.transformer_mode,
            height=self.height,
            width=self.width,
        )


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
            model_source = self.model_id
            if not Path(model_source).exists():
                try:
                    from huggingface_hub import try_to_load_from_cache
                    model_index = try_to_load_from_cache(model_source, filename="model_index.json", revision="main")
                    if model_index:
                        snapshot = Path(model_index).parent
                        required = (
                            "model_index.json", "scheduler/scheduler_config.json",
                            "unet/config.json", "vae/config.json",
                            "text_encoder/config.json",
                            "tokenizer/vocab.json", "tokenizer/merges.txt",
                            "tokenizer/tokenizer_config.json",
                        )
                        component_files = (
                            ("unet/diffusion_pytorch_model.safetensors", "unet/diffusion_pytorch_model.fp16.safetensors"),
                            ("vae/diffusion_pytorch_model.safetensors", "vae/diffusion_pytorch_model.fp16.safetensors"),
                            ("text_encoder/model.safetensors", "text_encoder/model.fp16.safetensors"),
                        )
                        if all((snapshot / part).exists() for part in required) and all(any((snapshot / part).exists() for part in alternatives) for alternatives in component_files):
                            model_source = str(snapshot)
                except Exception:
                    pass
            load_options = {"torch_dtype": self.dtype, "safety_checker": None}
            if self.model_id in {"stabilityai/sd-turbo", "stabilityai/sdxl-turbo", "stabilityai/stable-diffusion-xl-base-1.0"}:
                load_options["variant"] = "fp16"
            self._pipe = DiffusionPipeline.from_pretrained(model_source, **load_options)
            # SD 1.5 repositories commonly default to PNDM. PNDM's warm-up
            # history is not restartable after a latent intervention, which
            # causes long-horizon re-entry artifacts. DDIM preserves the same
            # model while providing a deterministic, restartable schedule.
            if type(self._pipe.scheduler).__name__ == "PNDMScheduler":
                self._pipe.scheduler = DDIMScheduler.from_config(self._pipe.scheduler.config)
            self._pipe = self._pipe.to(self.device)
            self._pipe.set_progress_bar_config(disable=True)
        return self._pipe

    def _effective_guidance(self, requested: float) -> float:
        # SD-Turbo is guidance-distilled. The positive branch is selected by
        # CFG=1; applying the UI's ordinary SD1.5 CFG=7.5 overdrives it and
        # produces the black previews caught by the real regression.
        return 1.0 if self.model_id == "stabilityai/sd-turbo" else requested

    def _image_mask(self, composite: str | None, height: int, width: int) -> torch.Tensor | None:
        if not composite:
            return None
        try:
            header, payload = composite.split(",", 1)
            if header.startswith("data:image/") and not header.startswith("data:image/svg+xml"):
                raw = base64.b64decode(payload)
                from PIL import Image
                image = Image.open(io.BytesIO(raw)).convert("L").resize((width, height))
                values = torch.tensor(list(image.getdata()), dtype=torch.float32).reshape(height, width) / 255.0
                return values.to(device=self.device, dtype=self.dtype).view(1, 1, height, width)
        except Exception:
            pass
        decoded = unquote(composite.split(",", 1)[1] if "," in composite else composite)
        match = re.search(r'points="([^"]+)', decoded)
        if not match:
            return None
        mask = torch.zeros((1, 1, height, width), device=self.device, dtype=self.dtype)
        for point in match.group(1).split():
            values = point.split(",")
            if len(values) < 2:
                continue
            x = min(max(int(float(values[0]) / 100 * width), 0), width - 1)
            y = min(max(int(float(values[1]) / 100 * height), 0), height - 1)
            mask[:, :, max(0, y - 3):min(height, y + 4), max(0, x - 3):min(width, x + 4)] = 1
        return mask

    def _guide_mask(self, composite: str | None, imported_image: str | None, erase_mask: str | None, height: int, width: int) -> torch.Tensor | None:
        draw_mask = self._image_mask(composite, height, width)
        imported_mask = self._image_mask(imported_image, height, width)
        if erase_mask and imported_mask is not None:
            try:
                import json
                for point in json.loads(erase_mask):
                    if len(point) < 2:
                        continue
                    x = min(max(int(float(point[0]) / 100 * width), 0), width - 1)
                    y = min(max(int(float(point[1]) / 100 * height), 0), height - 1)
                    imported_mask[:, :, max(0, y - 4):min(height, y + 5), max(0, x - 4):min(width, x + 5)] = 0
            except (TypeError, ValueError, json.JSONDecodeError):
                pass
        masks = [mask for mask in (draw_mask, imported_mask) if mask is not None]
        if not masks:
            return None
        return torch.maximum(masks[0], masks[1]) if len(masks) == 2 else masks[0]

    def _encode_prompt(self, pipe, prompt: str, height: int, width: int):
        encoded = pipe.encode_prompt(
            prompt=prompt,
            device=self.device,
            num_images_per_prompt=1,
            do_classifier_free_guidance=True,
        )
        positive, negative = encoded[:2]
        added = None
        # SDXL returns pooled prompt embeddings in addition to token embeds.
        # The UNet requires both pooled text and six crop/size time ids.
        if len(encoded) >= 4:
            pooled, negative_pooled = encoded[2:4]
            projection_dim = getattr(getattr(pipe, "text_encoder_2", None), "config", None)
            projection_dim = getattr(projection_dim, "projection_dim", None)
            if projection_dim is not None and hasattr(pipe, "_get_add_time_ids"):
                time_ids = pipe._get_add_time_ids(
                    (height, width), (0, 0), (height, width),
                    dtype=positive.dtype, text_encoder_projection_dim=projection_dim,
                )
                added = {
                    "text_embeds": torch.cat([negative_pooled, pooled]),
                    "time_ids": time_ids.to(self.device).repeat(2, 1),
                }
        return positive, negative, added

    def start(self, prompt: str, seed: int, steps: int = 8, guidance_scale: float = 7.5, guide_composite: str | None = None, imported_image: str | None = None, guide_erase_mask: str | None = None, guide_influence: float = 0.0) -> DiffusionState:
        with self._lock:
            pipe = self._pipeline()
            do_cfg = True
            height = pipe.unet.config.sample_size * pipe.vae_scale_factor
            width = height
            positive, negative, added = self._encode_prompt(pipe, prompt, height, width)
            generator = torch.Generator(device="cpu").manual_seed(seed)
            latents = pipe.prepare_latents(
                1, pipe.unet.config.in_channels, height, width,
                self.dtype, self.device, generator,
            )
            pipe.scheduler.set_timesteps(steps, device=self.device)
            guide_mask = self._guide_mask(guide_composite, imported_image, guide_erase_mask, latents.shape[-2], latents.shape[-1])
            return DiffusionState(prompt=prompt, latents=latents, prompt_embeds=positive, negative_prompt_embeds=negative, added_cond_kwargs=added, timesteps=pipe.scheduler.timesteps.detach().clone(), guide_mask=guide_mask, guide_influence=guide_influence, guide_composite=guide_composite, imported_image=imported_image, guide_erase_mask=guide_erase_mask, guidance_scale=self._effective_guidance(guidance_scale), requested_steps=steps)

    def update_conditions(self, state: DiffusionState, prompt: str, guide_composite: str | None, imported_image: str | None, guide_erase_mask: str | None, guide_influence: float, guidance_scale: float) -> None:
        """Change conditions without throwing away the retained latent state."""
        with self._lock:
            pipe = self._pipeline()
            positive, negative, added = self._encode_prompt(pipe, prompt, state.latents.shape[-1] * pipe.vae_scale_factor, state.latents.shape[-2] * pipe.vae_scale_factor)
            state.prompt = prompt
            state.prompt_embeds = positive
            state.negative_prompt_embeds = negative
            state.added_cond_kwargs = added
            state.guide_composite = guide_composite
            state.imported_image = imported_image
            state.guide_erase_mask = guide_erase_mask
            state.guide_influence = guide_influence
            state.guidance_scale = self._effective_guidance(guidance_scale)
            state.guide_mask = self._guide_mask(guide_composite, imported_image, guide_erase_mask, state.latents.shape[-2], state.latents.shape[-1])

    def _preview(self, pipe, latents: torch.Tensor) -> str:
        with torch.no_grad():
            # SDXL VAEs frequently overflow in fp16 on Apple MPS. Decode in
            # float32 so an otherwise valid latent is not rendered as black.
            decode_latents = latents
            if self.model_id in {"stabilityai/sdxl-turbo", "stabilityai/stable-diffusion-xl-base-1.0"}:
                decode_latents = latents.float()
                pipe.vae.to(dtype=torch.float32)
            decoded = pipe.vae.decode(decode_latents / pipe.vae.config.scaling_factor, return_dict=False)[0]
        decoded = torch.nan_to_num(decoded, nan=0.0, posinf=1.0, neginf=-1.0)
        image = ((decoded / 2 + 0.5).clamp(0, 1) * 255).byte()[0].permute(1, 2, 0).cpu().numpy()
        from PIL import Image
        buffer = io.BytesIO()
        Image.fromarray(image).save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

    def _reset_scheduler(self, pipe, steps: int) -> None:
        """Clear mutable solver history before reopening an exhausted stream."""
        pipe.scheduler.set_timesteps(steps, device=self.device)
        if hasattr(pipe.scheduler, "_step_index"):
            pipe.scheduler._step_index = None
        if hasattr(pipe.scheduler, "_begin_index"):
            pipe.scheduler._begin_index = None
        if hasattr(pipe.scheduler, "model_outputs"):
            pipe.scheduler.model_outputs = [None] * len(pipe.scheduler.model_outputs)
        if hasattr(pipe.scheduler, "lower_order_nums"):
            pipe.scheduler.lower_order_nums = 0

    def advance(self, state: DiffusionState, rejection_mask: list[list[float]] | None = None, rejection_strength: float = 0.0, exploration_strength: float = 0.04, temperature: float = 0.7, brush_size: int = 34) -> tuple[str, int, int]:
        started = time.perf_counter()
        with self._lock:
            pipe = self._pipeline()
            brush_radius = max(1, round(float(brush_size) / 12))
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
                            mask[:, :, max(0, y - brush_radius):min(mask.shape[-2], y + brush_radius + 1), max(0, x - brush_radius):min(mask.shape[-1], x + brush_radius + 1)] = 1
                    # Re-noise with the scheduler so the latent remains in
                    # the model's expected scale; replacing it with raw noise
                    # produces near-black previews after intervention.
                    restart_noise = torch.randn_like(state.latents) * min(max(float(temperature), 0.0), 2.0)
                    # Re-open near the current terminal state, not from the
                    # high-noise initial timestep the user already explored.
                    exploration = min(max(float(exploration_strength), 0.0), 1.0)
                    state.exploration_cycle += 1
                    restart_index = max(
                        len(state.timesteps) - 2
                        - round(exploration * max(len(state.timesteps) - 2, 0)),
                        0,
                    )
                    renoised = pipe.scheduler.add_noise(state.latents, restart_noise, state.timesteps[restart_index].reshape(1))
                    alpha = min(float(rejection_strength), 1.0)
                    state.latents = state.latents * (1 - mask * alpha) + renoised * (mask * alpha)
                else:
                    restart_noise = torch.randn_like(state.latents) * min(max(float(temperature), 0.0), 2.0)
                    exploration = min(max(float(exploration_strength), 0.0), 1.0)
                    state.exploration_cycle += 1
                    restart_index = max(
                        len(state.timesteps) - 2
                        - round(exploration * max(len(state.timesteps) - 2, 0)),
                        0,
                    )
                    renoised = pipe.scheduler.add_noise(state.latents, restart_noise, state.timesteps[restart_index].reshape(1))
                    if type(pipe.scheduler).__name__ == "DDIMScheduler":
                        state.latents = state.latents * (1 - exploration) + renoised * exploration
                    else:
                        state.latents = renoised
                self._reset_scheduler(pipe, state.requested_steps)
                state.timesteps = pipe.scheduler.timesteps.detach().clone()
                state.step_index = restart_index
            timestep = state.timesteps[state.step_index]
            latent_input = torch.cat([state.latents] * 2)
            latent_input = pipe.scheduler.scale_model_input(latent_input, timestep)
            embeds = torch.cat([state.negative_prompt_embeds, state.prompt_embeds])
            with torch.no_grad():
                unet_kwargs = {"encoder_hidden_states": embeds, "return_dict": False}
                if state.added_cond_kwargs is not None:
                    unet_kwargs["added_cond_kwargs"] = state.added_cond_kwargs
                noise = pipe.unet(latent_input, timestep, **unet_kwargs)[0]
            uncond, text = noise.chunk(2)
            noise = uncond + state.guidance_scale * (text - uncond)
            preview_latents = None
            if hasattr(pipe.scheduler, "alphas_cumprod"):
                timestep_index = int(timestep.item())
                alpha = pipe.scheduler.alphas_cumprod[timestep_index].to(state.latents.device, state.latents.dtype)
                preview_latents = (state.latents - (1 - alpha).sqrt() * noise) / alpha.sqrt()
            state.latents = pipe.scheduler.step(noise, timestep, state.latents, return_dict=False)[0]
            if state.guide_mask is not None and state.guide_influence > 0:
                # TinySD has no ControlNet; apply the Guide as a bounded
                # spatial latent bias so the submitted guide has a real,
                # observable effect without destabilising the image.
                # Keep a photo guide as a bounded condition. Adding a large
                # positive value on every denoise step accumulates and can
                # wash out or darken the whole image after long exploration.
                state.latents = state.latents + state.guide_mask * min(state.guide_influence, 1.0) * 0.02
            if rejection_mask and rejection_strength > 0:
                mask = torch.zeros((1, 1, state.latents.shape[-2], state.latents.shape[-1]), device=state.latents.device, dtype=state.latents.dtype)
                for point in rejection_mask:
                    if len(point) >= 2:
                        x = min(max(int(float(point[0]) / 100 * mask.shape[-1]), 0), mask.shape[-1] - 1)
                        y = min(max(int(float(point[1]) / 100 * mask.shape[-2]), 0), mask.shape[-2] - 1)
                        mask[:, :, max(0, y - brush_radius):min(mask.shape[-2], y + brush_radius + 1), max(0, x - brush_radius):min(mask.shape[-1], x + brush_radius + 1)] = 1
                # Re-noise at the current scheduler timestep. This pushes the
                # brushed area out of its current basin more decisively while
                # preserving the surrounding latent solution.
                current_noise = torch.randn_like(state.latents) * min(max(float(temperature), 0.0), 2.0)
                current_timestep = state.timesteps[state.step_index].reshape(1)
                renoised = pipe.scheduler.add_noise(state.latents, current_noise, current_timestep)
                # Keep a rejection pulse strong enough to be visible, but
                # avoid injecting almost pure noise into the persistent
                # latent. High alpha values leave colored artifacts that
                # amplify during later Explore re-entry cycles.
                alpha = min(0.2 + float(rejection_strength) * 0.4, 0.6)
                state.latents = state.latents * (1 - mask * alpha) + renoised * (mask * alpha)
            # A malformed/overstrong intervention must not poison the VAE
            # decode and turn the entire preview black.
            state.latents = torch.nan_to_num(state.latents, nan=0.0, posinf=4.0, neginf=-4.0).clamp(-4.0, 4.0)
            state.step_index += 1
            return self._preview(pipe, preview_latents if preview_latents is not None else state.latents), round((time.perf_counter() - started) * 1000), state.step_index


class TransformerDiffusionRuntime(TinySDRuntime):
    """Stateful adapter for FLUX and Stable Diffusion 3 Transformer pipelines.

    These models do not expose an SD UNet. Their packed/Transformer latents
    are kept in the same session state, so the API still advances one denoise
    step per request and can apply momentary guide/brush interventions.
    """

    def __init__(self, model_id: str) -> None:
        super().__init__(model_id)
        self.mode = "flux" if model_id.startswith("black-forest-labs/FLUX") else "sd3"

    def _pipeline(self):
        if self._pipe is None:
            cls = FluxPipeline if self.mode == "flux" else StableDiffusion3Pipeline
            self._pipe = cls.from_pretrained(self.model_id, torch_dtype=self.dtype, use_safetensors=True)
            self._pipe = self._pipe.to(self.device)
            self._pipe.set_progress_bar_config(disable=True)
        return self._pipe

    def _encode_transformer_prompt(self, pipe, prompt: str):
        if self.mode == "flux":
            positive, pooled, text_ids = pipe.encode_prompt(
                prompt=prompt, prompt_2=prompt, device=self.device,
                num_images_per_prompt=1, max_sequence_length=512,
            )
            return {
                "positive": positive, "negative": None, "pooled": pooled,
                "negative_pooled": None, "text_ids": text_ids,
                "negative_text_ids": None,
            }
        positive, negative, pooled, negative_pooled = pipe.encode_prompt(
            prompt=prompt, prompt_2=prompt, prompt_3=prompt,
            negative_prompt="", negative_prompt_2="", negative_prompt_3="",
            device=self.device, num_images_per_prompt=1,
            do_classifier_free_guidance=True, max_sequence_length=256,
        )
        return {
            "positive": positive, "negative": negative, "pooled": pooled,
            "negative_pooled": negative_pooled, "text_ids": None,
            "negative_text_ids": None,
        }

    def start(self, prompt: str, seed: int, steps: int = 8, guidance_scale: float = 7.5, guide_composite: str | None = None, imported_image: str | None = None, guide_erase_mask: str | None = None, guide_influence: float = 0.0) -> DiffusionState:
        with self._lock:
            pipe = self._pipeline()
            height = width = 512
            encoded = self._encode_transformer_prompt(pipe, prompt)
            generator = torch.Generator(device="cpu").manual_seed(seed)
            channels = pipe.transformer.config.in_channels // 4 if self.mode == "flux" else pipe.transformer.config.in_channels
            prepared = pipe.prepare_latents(1, channels, height, width, encoded["positive"].dtype, self.device, generator)
            if self.mode == "flux":
                latents, image_ids = prepared
                image_seq_len = latents.shape[1]
                mu = calculate_shift(image_seq_len, pipe.scheduler.config.get("base_image_seq_len", 256), pipe.scheduler.config.get("max_image_seq_len", 4096), pipe.scheduler.config.get("base_shift", 0.5), pipe.scheduler.config.get("max_shift", 1.15))
                timesteps, _ = flux_retrieve_timesteps(pipe.scheduler, steps, self.device, mu=mu)
            else:
                latents, image_ids = prepared, None
                timesteps, _ = sd3_retrieve_timesteps(pipe.scheduler, steps, self.device)
            guide_mask = self._guide_mask(guide_composite, imported_image, guide_erase_mask, latents.shape[-2] if latents.ndim == 4 else height // 8, latents.shape[-1] if latents.ndim == 4 else width // 8)
            return DiffusionState(
                prompt=prompt, latents=latents, prompt_embeds=encoded["positive"],
                negative_prompt_embeds=encoded["negative"] if encoded["negative"] is not None else encoded["positive"].detach().clone(),
                pooled_prompt_embeds=encoded["pooled"], negative_pooled_prompt_embeds=encoded["negative_pooled"],
                text_ids=encoded["text_ids"], negative_text_ids=encoded["negative_text_ids"], latent_image_ids=image_ids,
                timesteps=timesteps.detach().clone(), step_index=0, guide_mask=guide_mask,
                guide_influence=guide_influence, guide_composite=guide_composite, imported_image=imported_image,
                guide_erase_mask=guide_erase_mask, guidance_scale=guidance_scale, requested_steps=steps,
                transformer_mode=self.mode, height=height, width=width,
            )

    def update_conditions(self, state: DiffusionState, prompt: str, guide_composite: str | None, imported_image: str | None, guide_erase_mask: str | None, guide_influence: float, guidance_scale: float) -> None:
        with self._lock:
            encoded = self._encode_transformer_prompt(self._pipeline(), prompt)
            state.prompt = prompt
            state.prompt_embeds = encoded["positive"]
            state.negative_prompt_embeds = encoded["negative"] if encoded["negative"] is not None else encoded["positive"].detach().clone()
            state.pooled_prompt_embeds = encoded["pooled"]
            state.negative_pooled_prompt_embeds = encoded["negative_pooled"]
            state.text_ids, state.negative_text_ids = encoded["text_ids"], encoded["negative_text_ids"]
            state.guide_composite, state.imported_image, state.guide_erase_mask = guide_composite, imported_image, guide_erase_mask
            state.guide_influence, state.guidance_scale = guide_influence, guidance_scale
            h, w = (state.latents.shape[-2], state.latents.shape[-1]) if state.latents.ndim == 4 else (state.height // 8, state.width // 8)
            state.guide_mask = self._guide_mask(guide_composite, imported_image, guide_erase_mask, h, w)

    def _intervention_mask(self, state: DiffusionState, points: list[list[float]] | None, strength: float, temperature: float) -> torch.Tensor | None:
        if not points or strength <= 0:
            return None
        if state.latents.ndim == 4:
            mask = torch.zeros((1, 1, state.latents.shape[-2], state.latents.shape[-1]), device=self.device, dtype=state.latents.dtype)
            radius = max(1, round(self._brush_size / 12)) if hasattr(self, "_brush_size") else 3
            for point in points:
                if len(point) >= 2:
                    x = min(max(int(float(point[0]) / 100 * mask.shape[-1]), 0), mask.shape[-1] - 1)
                    y = min(max(int(float(point[1]) / 100 * mask.shape[-2]), 0), mask.shape[-2] - 1)
                    mask[:, :, max(0, y-radius):min(mask.shape[-2], y+radius+1), max(0, x-radius):min(mask.shape[-1], x+radius+1)] = 1
            return mask
        # FLUX stores 2x2-packed tokens. Map the brush to the token grid.
        grid = int(state.latents.shape[1] ** 0.5)
        mask = torch.zeros((1, 1, grid, grid), device=self.device, dtype=state.latents.dtype)
        for point in points:
            if len(point) >= 2:
                x = min(max(int(float(point[0]) / 100 * grid), 0), grid - 1)
                y = min(max(int(float(point[1]) / 100 * grid), 0), grid - 1)
                mask[:, :, max(0, y-2):min(grid, y+3), max(0, x-2):min(grid, x+3)] = 1
        return mask.flatten(2).transpose(1, 2)

    def advance(self, state: DiffusionState, rejection_mask: list[list[float]] | None = None, rejection_strength: float = 0.0, exploration_strength: float = 0.04, temperature: float = 0.7, brush_size: int = 34) -> tuple[str, int, int]:
        started = time.perf_counter()
        with self._lock:
            pipe = self._pipeline()
            self._brush_size = brush_size
            if state.step_index >= len(state.timesteps):
                state.exploration_cycle += 1
                state.latents = state.latents + torch.randn_like(state.latents) * min(max(temperature, 0.0), 2.0) * max(exploration_strength, 0.01) * 0.1
                state.step_index = max(0, len(state.timesteps) - 2)
                self._reset_scheduler(pipe, state.requested_steps)
            timestep = state.timesteps[state.step_index]
            if self.mode == "flux":
                model_input = state.latents
                timestep_input = timestep.expand(model_input.shape[0]).to(model_input.dtype) / 1000
                kwargs = dict(hidden_states=model_input, timestep=timestep_input, pooled_projections=state.pooled_prompt_embeds, encoder_hidden_states=state.prompt_embeds, txt_ids=state.text_ids, img_ids=state.latent_image_ids, joint_attention_kwargs={}, return_dict=False)
                if getattr(pipe.transformer.config, "guidance_embeds", False):
                    kwargs["guidance"] = torch.full((model_input.shape[0],), state.guidance_scale, device=self.device, dtype=model_input.dtype)
                with torch.no_grad():
                    noise = pipe.transformer(**kwargs)[0]
            else:
                model_input = torch.cat([state.latents] * 2)
                timestep_input = timestep.expand(model_input.shape[0])
                with torch.no_grad():
                    noise = pipe.transformer(hidden_states=model_input, timestep=timestep_input, encoder_hidden_states=torch.cat([state.negative_prompt_embeds, state.prompt_embeds]), pooled_projections=torch.cat([state.negative_pooled_prompt_embeds, state.pooled_prompt_embeds]), joint_attention_kwargs={}, return_dict=False)[0]
                uncond, text = noise.chunk(2)
                noise = uncond + state.guidance_scale * (text - uncond)
            state.latents = pipe.scheduler.step(noise, timestep, state.latents, return_dict=False)[0]
            if state.guide_mask is not None and state.guide_influence > 0:
                guide = state.guide_mask
                if state.latents.ndim == 3:
                    guide = torch.nn.functional.interpolate(guide, size=(int(state.latents.shape[1] ** 0.5), int(state.latents.shape[1] ** 0.5)), mode="nearest").flatten(2).transpose(1, 2)
                state.latents = state.latents + guide * min(state.guide_influence, 1.0) * 0.02
            mask = self._intervention_mask(state, rejection_mask, rejection_strength, temperature)
            if mask is not None:
                noise = torch.randn_like(state.latents) * min(max(temperature, 0.0), 2.0)
                state.latents = state.latents * (1 - mask * 0.5) + (state.latents + noise * 0.1) * (mask * 0.5)
            state.latents = torch.nan_to_num(state.latents, nan=0.0, posinf=4.0, neginf=-4.0).clamp(-4.0, 4.0)
            state.step_index += 1
            return self._preview(pipe, state.latents), round((time.perf_counter() - started) * 1000), state.step_index

    def _preview(self, pipe, latents: torch.Tensor) -> str:
        with torch.no_grad():
            if self.mode == "flux":
                decoded_latents = pipe._unpack_latents(latents, self.height, self.width, pipe.vae_scale_factor)
                decoded_latents = decoded_latents / pipe.vae.config.scaling_factor + pipe.vae.config.shift_factor
            else:
                decoded_latents = latents / pipe.vae.config.scaling_factor + getattr(pipe.vae.config, "shift_factor", 0.0)
            decoded = pipe.vae.decode(decoded_latents.float(), return_dict=False)[0]
        decoded = torch.nan_to_num(decoded, nan=0.0, posinf=1.0, neginf=-1.0)
        image = ((decoded / 2 + 0.5).clamp(0, 1) * 255).byte()[0].permute(1, 2, 0).cpu().numpy()
        from PIL import Image
        buffer = io.BytesIO(); Image.fromarray(image).save(buffer, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")
