from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from backend.config import settings
from backend.routers import auth, catalog, orders, payments, reports

app = FastAPI(
    title=settings.app_name,
    description="API REST para administrar proveedores, catalogo, clientes, pedidos, pagos y reportes.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(catalog.router, prefix=settings.api_prefix)
app.include_router(orders.router, prefix=settings.api_prefix)
app.include_router(payments.router, prefix=settings.api_prefix)
app.include_router(reports.router, prefix=settings.api_prefix)

@app.get("/", tags=["Estado"])
def root():
    return {"mensaje": "API de gestion de revendedores activa", "documentacion": "/docs", "version": "1.0.0"}

@app.get("/health", tags=["Estado"])
def health():
    return {"estado": "ok"}

@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # No se devuelve al cliente el detalle interno de errores o credenciales.
    return JSONResponse(status_code=500, content={"detail": "Error interno del servidor"})
