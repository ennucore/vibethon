from pydantic import BaseModel
from typing import List


class OpenAI(BaseModel):
    gpt4: str = "openai/gpt-4"
    gpt4_0314: str = "openai/gpt-4-0314"
    gpt4_turbo: str = "openai/gpt-4-turbo"
    gpt4_turbo_1106: str = "openai/gpt-4-1106-preview"
    gpt4_turbo_preview: str = "openai/gpt-4-turbo-preview"
    gpt4o: str = "openai/gpt-4o"
    gpt4o_2024_05_13: str = "openai/gpt-4o-2024-05-13"
    gpt4o_2024_08_06: str = "openai/gpt-4o-2024-08-06"
    gpt4o_extended: str = "openai/gpt-4o:extended"
    gpt4o_mini: str = "openai/gpt-4o-mini"
    gpt4o_mini_2024_07_18: str = "openai/gpt-4o-mini-2024-07-18"
    gpt35_turbo: str = "openai/gpt-3.5-turbo"
    gpt35_turbo_0125: str = "openai/gpt-3.5-turbo-0125"
    gpt35_turbo_0613: str = "openai/gpt-3.5-turbo-0613"
    gpt35_turbo_1106: str = "openai/gpt-3.5-turbo-1106"
    gpt35_turbo_16k: str = "openai/gpt-3.5-turbo-16k"
    gpt35_turbo_instruct: str = "openai/gpt-3.5-turbo-instruct"
    chatgpt_4o_latest: str = "openai/chatgpt-4o-latest"


class Anthropic(BaseModel):
    claude3_opus: str = "anthropic/claude-3-opus"
    claude3_opus_beta: str = "anthropic/claude-3-opus:beta"
    claude3_sonnet: str = "anthropic/claude-3-sonnet"
    claude3_sonnet_beta: str = "anthropic/claude-3-sonnet:beta"
    claude3_haiku: str = "anthropic/claude-3-haiku"
    claude3_haiku_beta: str = "anthropic/claude-3-haiku:beta"
    claude35_sonnet: str = "anthropic/claude-3.5-sonnet-20240620"
    claude35_sonnet_beta: str = "anthropic/claude-3.5-sonnet-20240620:beta"
    claude2: str = "anthropic/claude-2"
    claude2_beta: str = "anthropic/claude-2:beta"
    claude2_1: str = "anthropic/claude-2.1"
    claude2_1_beta: str = "anthropic/claude-2.1:beta"
    claude2_0: str = "anthropic/claude-2.0"
    claude2_0_beta: str = "anthropic/claude-2.0:beta"


class Google(BaseModel):
    gemini_pro_15: str = "google/gemini-pro-1.5"
    gemini_flash_15: str = "google/gemini-flash-1.5"
    gemma_2_27b: str = "google/gemma-2-27b-it"
    gemma_2_9b: str = "google/gemma-2-9b-it"
    gemma_2_9b_free: str = "google/gemma-2-9b-it:free"


class Meta(BaseModel):
    llama3_8b_instruct: str = "meta-llama/llama-3-8b-instruct"
    llama3_70b_instruct: str = "meta-llama/llama-3-70b-instruct"
    llama31_8b_instruct: str = "meta-llama/llama-3.1-8b-instruct"
    llama31_8b_instruct_free: str = "meta-llama/llama-3.1-8b-instruct:free"
    llama31_70b_instruct: str = "meta-llama/llama-3.1-70b-instruct"
    llama31_405b_instruct: str = "meta-llama/llama-3.1-405b-instruct"
    llama31_405b_base: str = "meta-llama/llama-3.1-405b"
    llama_guard_2_8b: str = "meta-llama/llama-guard-2-8b"


class Mistral(BaseModel):
    mistral_7b_instruct: str = "mistralai/mistral-7b-instruct"
    mistral_7b_instruct_free: str = "mistralai/mistral-7b-instruct:free"
    mistral_7b_instruct_v01: str = "mistralai/mistral-7b-instruct-v0.1"
    mistral_7b_instruct_v02: str = "mistralai/mistral-7b-instruct-v0.2"
    mistral_7b_instruct_v03: str = "mistralai/mistral-7b-instruct-v0.3"
    mistral_nemo: str = "mistralai/mistral-nemo"
    mistral_nemo_free: str = "mistralai/mistral-nemo:free"
    mistral_large: str = "mistralai/mistral-large"
    mistral_medium: str = "mistralai/mistral-medium"
    mistral_small: str = "mistralai/mistral-small"
    mistral_tiny: str = "mistralai/mistral-tiny"
    mixtral_8x7b_instruct: str = "mistralai/mixtral-8x7b-instruct"
    mixtral_8x22b_instruct: str = "mistralai/mixtral-8x22b-instruct"


class Cohere(BaseModel):
    command: str = "cohere/command"
    command_r: str = "cohere/command-r"
    command_r_03_2024: str = "cohere/command-r-03-2024"
    command_r_plus: str = "cohere/command-r-plus"
    command_r_plus_04_2024: str = "cohere/command-r-plus-04-2024"


class Perplexity(BaseModel):
    llama31_sonar_large_online: str = "perplexity/llama-3.1-sonar-large-128k-online"
    llama31_sonar_small_online: str = "perplexity/llama-3.1-sonar-small-128k-online"


class Microsoft(BaseModel):
    phi3_mini_128k: str = "microsoft/phi-3-mini-128k-instruct"
    phi3_medium_128k: str = "microsoft/phi-3-medium-128k-instruct"
    wizardlm_2_8x22b: str = "microsoft/wizardlm-2-8x22b"


class Creative(BaseModel):
    mythomax_13b: str = "gryphe/mythomax-l2-13b"
    mythalion_13b: str = "pygmalionai/mythalion-13b"
    goliath_120b: str = "alpindale/goliath-120b"
    magnum_72b: str = "alpindale/magnum-72b"
    toppy_m_7b: str = "undi95/toppy-m-7b"
    remm_slerp_13b: str = "undi95/remm-slerp-l2-13b"
    midnight_rose_70b: str = "sophosympatheia/midnight-rose-70b"
    noromaid_20b: str = "neversleep/noromaid-20b"
    fimbulvetr_11b_v2: str = "sao10k/fimbulvetr-11b-v2"
    llama3_lumimaid_8b: str = "neversleep/llama-3-lumimaid-8b"
    llama3_lumimaid_70b: str = "neversleep/llama-3-lumimaid-70b"
    llama3_euryale_70b: str = "sao10k/l3-euryale-70b"
    llama3_lunaris_8b: str = "sao10k/l3-lunaris-8b"
    weaver_alpha: str = "mancer/weaver"


class Specialized(BaseModel):
    nous_hermes_2_pro_llama3_8b: str = "nousresearch/hermes-2-pro-llama-3-8b"
    nous_hermes_2_mixtral_8x7b_dpo: str = "nousresearch/nous-hermes-2-mixtral-8x7b-dpo"
    dolphin_mixtral_8x22b: str = "cognitivecomputations/dolphin-mixtral-8x22b"
    qwen_2_72b_instruct: str = "qwen/qwen-2-72b-instruct"
    yi_large: str = "01-ai/yi-large"
    mistral_nemo_celeste_12b: str = "nothingiisreal/mn-celeste-12b"
    starcannon_12b: str = "aetherwiing/mn-starcannon-12b"


class OpenRouter(BaseModel):
    auto: str = "openrouter/auto"


class Models(BaseModel):
    openai: OpenAI = OpenAI()
    anthropic: Anthropic = Anthropic()
    google: Google = Google()
    meta: Meta = Meta()
    mistral: Mistral = Mistral()
    cohere: Cohere = Cohere()
    perplexity: Perplexity = Perplexity()
    microsoft: Microsoft = Microsoft()
    creative: Creative = Creative()
    specialized: Specialized = Specialized()
    openrouter: OpenRouter = OpenRouter()

    @property
    def flagship(self) -> List[str]:
        return [
            self.openai.gpt4o,
            self.anthropic.claude3_opus,
            self.anthropic.claude35_sonnet,
            self.google.gemini_pro_15,
            self.mistral.mistral_large,
            self.meta.llama31_405b_instruct
        ]

    @property
    def budget(self) -> List[str]:
        return [
            self.openai.gpt35_turbo,
            self.openai.gpt4o_mini,
            self.anthropic.claude3_haiku,
            self.google.gemini_flash_15,
            self.mistral.mistral_7b_instruct,
            self.meta.llama31_8b_instruct
        ]

    @property
    def free(self) -> List[str]:
        return [
            self.openai.gpt35_turbo,
            self.mistral.mistral_7b_instruct_free,
            self.mistral.mistral_nemo_free,
            self.meta.llama31_8b_instruct_free,
            self.google.gemma_2_9b_free
        ]

    @property
    def creative_models(self) -> List[str]:
        return [
            self.creative.mythomax_13b,
            self.creative.mythalion_13b,
            self.creative.goliath_120b,
            self.creative.magnum_72b,
            self.creative.midnight_rose_70b,
            self.creative.llama3_lumimaid_70b,
            self.creative.llama3_euryale_70b,
            self.creative.fimbulvetr_11b_v2
        ]

    @property
    def coding(self) -> List[str]:
        return [
            self.openai.gpt4o,
            self.anthropic.claude35_sonnet,
            self.mistral.mistral_large,
            self.meta.llama31_405b_instruct,
            self.specialized.qwen_2_72b_instruct
        ]

    @property
    def multimodal(self) -> List[str]:
        return [
            self.openai.gpt4o,
            self.openai.gpt4_turbo,
            self.anthropic.claude3_opus,
            self.anthropic.claude3_sonnet,
            self.anthropic.claude3_haiku,
            self.google.gemini_pro_15,
            self.google.gemini_flash_15
        ]

    @property
    def small(self) -> List[str]:
        return [
            self.openai.gpt4o_mini,
            self.anthropic.claude3_haiku,
            self.google.gemini_flash_15,
            self.mistral.mistral_7b_instruct,
            self.meta.llama3_8b_instruct,
            self.microsoft.phi3_mini_128k
        ]

    @property
    def large_context(self) -> List[str]:
        return [
            self.anthropic.claude3_opus,
            self.anthropic.claude3_sonnet,
            self.anthropic.claude3_haiku,
            self.google.gemini_pro_15,
            self.google.gemini_flash_15,
            self.meta.llama31_405b_instruct,
            self.mistral.mistral_nemo
        ]

    def get_models_by_category(self, category: str) -> List[str]:
        categories = {
            'flagship': self.flagship,
            'budget': self.budget,
            'free': self.free,
            'creative': self.creative_models,
            'coding': self.coding,
            'multimodal': self.multimodal,
            'small': self.small,
            'large_context': self.large_context
        }
        return categories.get(category.lower(), [])


models = Models()
