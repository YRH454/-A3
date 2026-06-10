from app.services.llm import generate_glm_image
import os
print("Key:", bool(os.getenv("GLM_IMAGE_API_KEY")))
url = generate_glm_image("a cute whale", "1024x1024")
print("Result:", url)
