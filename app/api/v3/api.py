from fastapi import APIRouter

from app.api.v3.routers import seller_products

routers: list[APIRouter] = [seller_products.router]
