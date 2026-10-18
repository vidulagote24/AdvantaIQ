from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.routes import router as v1_router

app = FastAPI(
    title='AdvantaIQ Advisor Intelligence API',
    description='API for AdvantaIQ - AI-powered financial advisor intelligence platform',
    version='1.0.0-milestone1'
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173', 'http://localhost:3000'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Register routes
app.include_router(v1_router, prefix='/api/v1')

@app.get('/')
def root():
    return {
        'service': 'AdvantaIQ Advisor Intelligence API',
        'status': 'online',
        'documentation': '/docs'
    }

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app.main:app', host='127.0.0.1', port=8000, reload=True)
