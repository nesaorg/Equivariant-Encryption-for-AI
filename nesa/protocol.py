from typing import Optional, Dict, List, Any, Union, Set
import msgspec 
from typing_extensions import Annotated
from nesa.logger import logger
from enum import Enum, IntEnum, StrEnum, auto
from functools import cached_property
import copy


_MAX_TEMP = 1e-2
_SAMPLING_EPS = 1e-5

class Message(msgspec.Struct,
              omit_defaults=True,
              dict=True):
    content: str
    role: Optional[str]
    
class SamplingType(IntEnum):
    GREEDY = 0
    RANDOM = 1
    RANDOM_SEED = 2

class Role(StrEnum):
    ASSISTANT = auto()
    USER = auto()
    AI = auto()

class LLMParams(msgspec.Struct):

    n: int = 1
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    repetition_penalty: float = 1.0
    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = -1
    min_p: float = 0.0
    seed: Optional[int] = None
    stop_token_ids: Optional[List[int]] = None
    ignore_eos: bool = False
    max_tokens: Optional[int] = 16
    min_tokens: int = 0
    skip_special_tokens: bool = True
    detokenize: bool = True # will use the encrypted tokenizer to decrypt
    truncate_prompt_tokens: Optional[Annotated[int, msgspec.Meta(ge=1)]] = None


    @staticmethod
    def from_optional(
        n: Optional[int] = 1,
        presence_penalty: Optional[float] = 0.0,
        frequency_penalty: Optional[float] = 0.0,
        repetition_penalty: Optional[float] = 1.0,
        temperature: Optional[float] = 1.0,
        top_p: Optional[float] = 1.0,
        top_k: int = -1,
        min_p: float = 0.0,
        seed: Optional[int] = None,
        stop_token_ids: Optional[List[int]] = None,
        ignore_eos: bool = False,
        max_tokens: Optional[int] = 16,
        min_tokens: int = 0,
        detokenize: bool = True,
        skip_special_tokens: bool = True,
        truncate_prompt_tokens: Optional[Annotated[int,
                                                   msgspec.Meta(ge=1)]] = None) -> "LLMParams":
        

        return LLMParams(
            n=1 if n is None else n,
            presence_penalty=0.0
            if presence_penalty is None else presence_penalty,
            frequency_penalty=0.0
            if frequency_penalty is None else frequency_penalty,
            repetition_penalty=1.0
            if repetition_penalty is None else repetition_penalty,
            temperature=1.0 if temperature is None else temperature,
            top_p=1.0 if top_p is None else top_p,
            top_k=top_k,
            min_p=min_p,
            seed=seed,
            stop_token_ids=stop_token_ids,
            ignore_eos=ignore_eos,
            max_tokens=max_tokens,
            min_tokens=min_tokens,
            detokenize=detokenize,
            skip_special_tokens=skip_special_tokens,
            truncate_prompt_tokens=truncate_prompt_tokens)

    def __post_init__(self) -> None:

        if 0 < self.temperature < _MAX_TEMP:
            logger.warning(
                "temperature %s is less than %s, which may cause numerical "
                "errors nan or inf in tensors. We have maxed it out to %s.",
                self.temperature, _MAX_TEMP, _MAX_TEMP)
            self.temperature = max(self.temperature, _MAX_TEMP)

        if self.seed == -1:
            self.seed = None
        else:
            self.seed = self.seed
            
        if self.stop_token_ids is None:
            self.stop_token_ids = []
        else:
            self.stop_token_ids = list(self.stop_token_ids)
        
        self._verify_args()

        if self.temperature < _SAMPLING_EPS:
            # zero temperature means greedy sampling.
            self.top_p = 1.0
            self.top_k = -1
            self.min_p = 0.0
            self._verify_greedy_sampling()

    def _verify_args(self) -> None:
        if not isinstance(self.n, int):
            raise ValueError(f"n must be an int, but is of "
                             f"type {type(self.n)}")
        if self.n < 1:
            raise ValueError(f"n must be at least 1, got {self.n}.")
        if not -2.0 <= self.presence_penalty <= 2.0:
            raise ValueError("presence_penalty must be in [-2, 2], got "
                             f"{self.presence_penalty}.")
        if not -2.0 <= self.frequency_penalty <= 2.0:
            raise ValueError("frequency_penalty must be in [-2, 2], got "
                             f"{self.frequency_penalty}.")
        if not 0.0 < self.repetition_penalty <= 2.0:
            raise ValueError("repetition_penalty must be in (0, 2], got "
                             f"{self.repetition_penalty}.")
        if self.temperature < 0.0:
            raise ValueError(
                f"temperature must be non-negative, got {self.temperature}.")
        if not 0.0 < self.top_p <= 1.0:
            raise ValueError(f"top_p must be in (0, 1], got {self.top_p}.")
        if self.top_k < -1 or self.top_k == 0:
            raise ValueError(f"top_k must be -1 (disable), or at least 1, "
                             f"got {self.top_k}.")
        if not isinstance(self.top_k, int):
            raise TypeError(
                f"top_k must be an integer, got {type(self.top_k).__name__}")
        if not 0.0 <= self.min_p <= 1.0:
            raise ValueError("min_p must be in [0, 1], got "
                             f"{self.min_p}.")
        if self.max_tokens is not None and self.max_tokens < 1:
            raise ValueError(
                f"max_tokens must be at least 1, got {self.max_tokens}.")
        if self.min_tokens < 0:
            raise ValueError(f"min_tokens must be greater than or equal to 0, "
                             f"got {self.min_tokens}.")
        if self.max_tokens is not None and self.min_tokens > self.max_tokens:
            raise ValueError(
                f"min_tokens must be less than or equal to "
                f"max_tokens={self.max_tokens}, got {self.min_tokens}.")


    def _verify_greedy_sampling(self) -> None:
        if self.n > 1:
            raise ValueError("n must be 1 when using greedy sampling, "
                             f"got {self.n}.")

    @cached_property
    def sampling_type(self) -> SamplingType:
        if self.temperature < _SAMPLING_EPS:
            return SamplingType.GREEDY
        if self.seed is not None:
            return SamplingType.RANDOM_SEED
        return SamplingType.RANDOM

class SessionID(msgspec.Struct,
                omit_defaults=True,
                dict=True):
    
    ee: bool
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class LLMInference(
    msgspec.Struct,
    omit_defaults=True,
    dict=True,
    forbid_unknown_fields=False
    ):
    
    stream: bool
    correlation_id: str
    messages: List[Message]
    model: str
    model_params: Optional[Union[LLMParams, Dict[str, Union[str, int, float]]]] = None
    session_id: Optional[SessionID] = None

class DeltaMessage(
    msgspec.Struct,
    omit_defaults=True,
    dict=True,
    forbid_unknown_fields=False
    ):
    
    role: Optional[str] = None
    content: Optional[Union[int,str]] = None

class Choice(
    msgspec.Struct,
    omit_defaults=True,
    dict=True,
    forbid_unknown_fields=False):
    
    index: int
    delta: DeltaMessage
    finish_reason: Optional[str]
    
class InferenceResponse(
    msgspec.Struct,
    omit_defaults=True,
    dict=True,
    forbid_unknown_fields=False):
    

    correlation_id: str
    model: str
    choices: list[Choice]
    object: Annotated[
        str, msgspec.Meta(pattern="^chat\\.completion\\.chunk$")
    ] = "chat.completion.chunk"
    session: Optional[SessionID] = None