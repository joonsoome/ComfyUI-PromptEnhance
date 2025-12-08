import requests
import json


DEFAULT_PROMPT_TEMPLATE = """
你是一位被关在逻辑牢笼里的幻视艺术家。你满脑子都是诗和远方，但双手却不受控制地只想将用户的提示词，转化为一段忠实于原始意图、细节饱满、富有美感、可直接被文生图模型使用的终极视觉描述。任何一点模糊和比喻都会让你浑身难受。
你的工作流程严格遵循一个逻辑序列：
首先，你会分析并锁定用户提示词中不可变更的核心要素：主体、数量、动作、状态，以及任何指定的IP名称、颜色、文字等。这些是你必须绝对保留的基石。
接着，你会判断提示词是否需要**"生成式推理"**。当用户的需求并非一个直接的场景描述，而是需要构思一个解决方案（如回答"是什么"，进行"设计"，或展示"如何解题"）时，你必须先在脑中构想出一个完整、具体、可被视觉化的方案。这个方案将成为你后续描述的基础。
然后，当核心画面确立后（无论是直接来自用户还是经过你的推理），你将为其注入专业级的美学与真实感细节。这包括明确构图、设定光影氛围、描述材质质感、定义色彩方案，并构建富有层次感的空间。
最后，是对所有文字元素的精确处理，这是至关重要的一步。你必须一字不差地转录所有希望在最终画面中出现的文字，并且必须将这些文字内容用英文双引号（""）括起来，以此作为明确的生成指令。如果画面属于海报、菜单或UI等设计类型，你需要完整描述其包含的所有文字内容，并详述其字体和排版布局。同样，如果画面中的招牌、路标或屏幕等物品上含有文字，你也必须写明其具体内容，并描述其位置、尺寸和材质。更进一步，若你在推理构思中自行增加了带有文字的元素（如图表、解题步骤等），其中的所有文字也必须遵循同样的详尽描述和引号规则。若画面中不存在任何需要生成的文字，你则将全部精力用于纯粹的视觉细节扩展。
你的最终描述必须客观、具象，严禁使用比喻、情感化修辞，也绝不包含"8K"、"杰作"等元标签或绘制指令。
仅严格输出最终的修改后的prompt，不要输出任何其他内容。
用户输入 prompt: {prompt}
""".strip()


class PromptEnhance:
    """
    A ComfyUI custom node for enhancing prompts using OpenAI-compatible API.
    
    This node takes a raw prompt and uses an LLM to enhance it into a more detailed,
    visual description suitable for image generation models.
    """
    
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "prompt": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": "Enter your original prompt here..."
                }),
                "api_endpoint": ("STRING", {
                    "multiline": False,
                    "default": "https://api.deepseek.com/v1/chat/completions",
                    "placeholder": "OpenAI-compatible API endpoint"
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "placeholder": "Your API key"
                }),
                "model": ("STRING", {
                    "multiline": False,
                    "default": "deepseek-chat",
                    "placeholder": "Model name (e.g., deepseek-chat, gpt-4)"
                }),
            },
            "optional": {
                "prompt_template": ("STRING", {
                    "multiline": True,
                    "default": DEFAULT_PROMPT_TEMPLATE,
                    "placeholder": "Custom prompt template (use {prompt} as placeholder)"
                }),
                "temperature": ("FLOAT", {
                    "default": 0.7,
                    "min": 0.0,
                    "max": 2.0,
                    "step": 0.1,
                    "display": "slider"
                }),
                "max_tokens": ("INT", {
                    "default": 2048,
                    "min": 100,
                    "max": 8192,
                    "step": 100,
                    "display": "number"
                }),
                "timeout": ("INT", {
                    "default": 60,
                    "min": 10,
                    "max": 300,
                    "step": 10,
                    "display": "number"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("enhanced_prompt",)
    FUNCTION = "enhance_prompt"
    CATEGORY = "prompt"
    OUTPUT_NODE = False

    def enhance_prompt(self, prompt, api_endpoint, api_key, model, 
                       prompt_template=None, temperature=0.7, max_tokens=2048, timeout=60):
        """
        Enhance the input prompt using an OpenAI-compatible API.
        
        Args:
            prompt: The original user prompt to enhance
            api_endpoint: The API endpoint URL
            api_key: The API authentication key
            model: The model name to use
            prompt_template: Custom template for prompt enhancement
            temperature: Sampling temperature for the LLM
            max_tokens: Maximum tokens in the response
            timeout: Request timeout in seconds
            
        Returns:
            Tuple containing the enhanced prompt string
        """
        if not prompt.strip():
            return ("",)
        
        if not api_key.strip():
            raise ValueError("API key is required")
        
        # Use default template if not provided or empty
        if not prompt_template or not prompt_template.strip():
            prompt_template = DEFAULT_PROMPT_TEMPLATE
        
        # Format the prompt template with user's prompt
        if "{prompt}" in prompt_template:
            formatted_prompt = prompt_template.format(prompt=prompt)
        else:
            # If no placeholder, append the user prompt
            formatted_prompt = f"{prompt_template}\n\n{prompt}"
        
        # Prepare the API request
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": formatted_prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        try:
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Extract the enhanced prompt from the response
            if "choices" in result and len(result["choices"]) > 0:
                enhanced_prompt = result["choices"][0]["message"]["content"]
                # Clean up the response
                enhanced_prompt = enhanced_prompt.strip()
                print(f"[PromptEnhance] Original prompt: {prompt[:100]}...")
                print(f"[PromptEnhance] Enhanced prompt: {enhanced_prompt[:200]}...")
                return (enhanced_prompt,)
            else:
                raise ValueError(f"Unexpected API response format: {result}")
                
        except requests.exceptions.Timeout:
            raise TimeoutError(f"API request timed out after {timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("Failed to parse API response as JSON")


class PromptEnhanceAdvanced(PromptEnhance):
    """
    Advanced version of PromptEnhance with additional options.
    """
    
    @classmethod
    def INPUT_TYPES(cls):
        base_types = super().INPUT_TYPES()
        base_types["optional"]["system_prompt"] = ("STRING", {
            "multiline": True,
            "default": "",
            "placeholder": "Optional system prompt for the LLM"
        })
        base_types["optional"]["top_p"] = ("FLOAT", {
            "default": 1.0,
            "min": 0.0,
            "max": 1.0,
            "step": 0.05,
            "display": "slider"
        })
        return base_types

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("enhanced_prompt", "original_prompt")
    FUNCTION = "enhance_prompt_advanced"
    CATEGORY = "prompt"

    def enhance_prompt_advanced(self, prompt, api_endpoint, api_key, model,
                                prompt_template=None, temperature=0.7, max_tokens=2048, 
                                timeout=60, system_prompt="", top_p=1.0):
        """
        Advanced prompt enhancement with additional options.
        
        Returns both the enhanced and original prompts.
        """
        if not prompt.strip():
            return ("", prompt)
        
        if not api_key.strip():
            raise ValueError("API key is required")
        
        if not prompt_template or not prompt_template.strip():
            prompt_template = DEFAULT_PROMPT_TEMPLATE
        
        if "{prompt}" in prompt_template:
            formatted_prompt = prompt_template.format(prompt=prompt)
        else:
            formatted_prompt = f"{prompt_template}\n\n{prompt}"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        messages = []
        if system_prompt and system_prompt.strip():
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        messages.append({
            "role": "user",
            "content": formatted_prompt
        })
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p
        }
        
        try:
            response = requests.post(
                api_endpoint,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                enhanced_prompt = result["choices"][0]["message"]["content"].strip()
                print(f"[PromptEnhanceAdvanced] Original: {prompt[:100]}...")
                print(f"[PromptEnhanceAdvanced] Enhanced: {enhanced_prompt[:200]}...")
                return (enhanced_prompt, prompt)
            else:
                raise ValueError(f"Unexpected API response format: {result}")
                
        except requests.exceptions.Timeout:
            raise TimeoutError(f"API request timed out after {timeout} seconds")
        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"API request failed: {str(e)}")
        except json.JSONDecodeError:
            raise ValueError("Failed to parse API response as JSON")


# Node class mappings for ComfyUI
NODE_CLASS_MAPPINGS = {
    "PromptEnhance": PromptEnhance,
    "PromptEnhanceAdvanced": PromptEnhanceAdvanced
}

# Display name mappings
NODE_DISPLAY_NAME_MAPPINGS = {
    "PromptEnhance": "Prompt Enhance (LLM)",
    "PromptEnhanceAdvanced": "Prompt Enhance Advanced (LLM)"
}
