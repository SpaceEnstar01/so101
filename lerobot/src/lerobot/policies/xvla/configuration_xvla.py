# Copyright 2025
# Minimal configuration wrapper for X-VLA model compatibility with lerobot

from dataclasses import dataclass, field

from lerobot.configs.policies import PreTrainedConfig
from lerobot.configs.types import FeatureType, NormalizationMode, PolicyFeature
from lerobot.optim.optimizers import AdamWConfig


@PreTrainedConfig.register_subclass("xvla")
@dataclass
class XVLAConfig(PreTrainedConfig):
    """
    Minimal configuration wrapper for X-VLA model.
    
    This is a placeholder configuration to allow lerobot to recognize
    the 'xvla' policy type. The actual model loading may require
    custom handling.
    """
    
    # Basic structure required by PreTrainedConfig
    n_obs_steps: int = 1
    chunk_size: int = 1
    n_action_steps: int = 1
    
    normalization_mapping: dict[str, NormalizationMode] = field(
        default_factory=lambda: {
            "VISUAL": NormalizationMode.IDENTITY,
            "STATE": NormalizationMode.MEAN_STD,
            "ACTION": NormalizationMode.MEAN_STD,
        }
    )
    
    # X-VLA specific parameters (from the model's config.json)
    # These fields are present in the model's config.json and need to be accepted
    _name_or_path: str | None = None
    model_type: str = "xvla"
    architectures: list[str] = field(default_factory=lambda: ["XVLA"])
    auto_map: dict[str, str] | None = None
    florence_config: dict | None = None
    
    action_mode: str = "ee6d"
    use_proprio: bool = True
    num_actions: int = 30
    hidden_size: int = 1024
    depth: int = 24
    num_heads: int = 16
    mlp_ratio: float = 4.0
    num_domains: int = 30
    len_soft_prompts: int = 32
    dim_time: int = 32
    max_len_seq: int = 512
    use_hetero_proj: bool = False
    soft_prompt_length: int = 32
    
    # Required abstract methods implementation
    @property
    def observation_delta_indices(self) -> list:
        return [0]
    
    @property
    def action_delta_indices(self) -> list:
        return list(range(self.chunk_size))
    
    @property
    def reward_delta_indices(self) -> None:
        return None
    
    def validate_features(self) -> None:
        """Validate input/output features. Placeholder for X-VLA."""
        pass
    
    def get_optimizer_preset(self) -> AdamWConfig:
        """Return optimizer preset. Placeholder for X-VLA."""
        return AdamWConfig(lr=1e-4)
    
    def get_scheduler_preset(self):
        """Return scheduler preset. Placeholder for X-VLA."""
        return None
