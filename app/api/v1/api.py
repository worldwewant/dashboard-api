"""
MIT License

Copyright (c) 2023 World We Want. Maintainers: Thomas Wood, https://fastdatascience.com, Zairon Jacobs, https://zaironjacobs.com.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.campaign_configurations import (
    router as campaign_configurations_router,
)
from app.api.v1.endpoints.campaigns import router as campaigns_router
from app.api.v1.endpoints.data import router as data_router
from app.api.v1.endpoints.geo_json_world import router as geo_json_world_router
from app.api.v1.endpoints.health_check import router as health_check_router
from app.api.v1.endpoints.info import router as info_router
from app.api.v1.endpoints.settings import router as settings_router
from app.api.v1.endpoints.topo_json import router as topo_json_router

api_router = APIRouter()
api_router.include_router(
    campaign_configurations_router, tags=["Campaigns Configurations"]
)
api_router.include_router(campaigns_router, tags=["Campaigns"])
api_router.include_router(auth_router, tags=["Authentication"])
api_router.include_router(data_router, tags=["Data"])
api_router.include_router(geo_json_world_router, tags=["GeoJSON World"])
api_router.include_router(topo_json_router, tags=["TopoJSON"])
api_router.include_router(settings_router, tags=["App Settings"])
api_router.include_router(health_check_router, tags=["Health Check"])
api_router.include_router(info_router, tags=["Info"])
