# Vercel API Handler - FastAPI Adapter
# This makes FastAPI work as Vercel serverless function

from main import app

# Vercel expects a handler function
def handler(request):
    return app(request)
