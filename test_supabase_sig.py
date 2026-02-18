
import inspect
from supabase import create_client

def test_signature():
    url = "https://example.supabase.co"
    key = "example-key"
    supabase = create_client(url, key)
    print("Sign up signature:", inspect.signature(supabase.auth.sign_up))

if __name__ == "__main__":
    test_signature()
