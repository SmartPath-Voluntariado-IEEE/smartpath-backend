import os

# Set default test environment variables before importing app modules
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_ANON_KEY", "dummy_anon_key_for_testing_purposes_only")
os.environ.setdefault("REDIRECT_URI", "http://localhost:3000")
