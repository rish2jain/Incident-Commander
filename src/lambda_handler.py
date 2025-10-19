"""
Lambda handler for Incident Commander FastAPI application.
"""

from mangum import Mangum
from src.main import app

# Create Lambda handler
handler = Mangum(app, lifespan="off")
