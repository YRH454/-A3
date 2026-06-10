from app.services.llm import generate_glm_image
from app.services.profile_db import get_profile
from app.agents.profile_agent import chat_deepseek, DIMENSIONS_ORDER

p = get_profile(0)
profile_data = p["profile"]
profile_text = "\n".join(f"- {label}£º{profile_data.get(key, '')}" for key, label, _ in DIMENSIONS_ORDER)

# Test prompt generation
resp = chat_deepseek([{"role": "system", "content": f"Based on this profile, write a short English prompt for an image.\nProfile:\n{profile_text}\nReturn only the prompt."}], temperature=0.7, max_tokens=100)
prompt = resp.choices[0].message.content.strip()
print(f"Prompt: {prompt}")

# Test image generation
url = generate_glm_image(prompt)
print(f"Image URL: {url}")
