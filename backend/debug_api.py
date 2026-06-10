import sys; sys.path.insert(0, "D:/Èí¼þ±­3Ìâ/backend")
from app.services.llm import generate_glm_image, chat_deepseek
from app.services.profile_db import get_profile
import os
os.environ["GLM_IMAGE_API_KEY"] = "52c952573ee845588939292efa66dadb.L6qU5KFBhRdUTJo7"

print("1. get_profile...")
p = get_profile(0)
if p:
    keys = list(p["profile"].keys())
    print(f"   OK, keys: {keys}")
    profile_text = "\n".join(f"- {k}: {p['profile'].get(k, '')}" for k in keys)
else:
    print("   No profile found")
    sys.exit(1)

print("2. chat_deepseek for prompt...")
try:
    resp = chat_deepseek([{"role": "system", "content": f"Write a short English prompt for an educational illustration.\nProfile:\n{profile_text}\nReturn only the prompt."}], temperature=0.7, max_tokens=100)
    prompt = resp.choices[0].message.content.strip()
    print(f"   Prompt: {prompt}")
except Exception as e:
    print(f"   ERROR: {e}")

print("3. generate_glm_image...")
try:
    url = generate_glm_image(prompt)
    print(f"   URL: {url}")
except Exception as e:
    print(f"   ERROR: {e}")
