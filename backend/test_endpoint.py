from app.api.profile import generate_profile_image
from app.database import query
# Check if user 0 has profile data
from app.services.profile_db import get_profile
p = get_profile(0)
print("Profile:", p is not None)
if p:
    print("Keys:", list(p["profile"].keys())[:5])
    print("First val:", list(p["profile"].values())[0][:50] if p["profile"] else "empty")
