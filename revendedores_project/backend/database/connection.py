import oracledb
from backend.config import settings


def get_connection():
    """Abre una conexion Oracle. Las credenciales provienen del entorno, nunca del codigo."""
    if not settings.oracle_user or not settings.oracle_password or not settings.oracle_dsn:
        raise RuntimeError("Faltan ORACLE_USER, ORACLE_PASSWORD u ORACLE_DSN en el archivo .env")
    params = {
        "user": settings.oracle_user,
        "password": settings.oracle_password,
        "dsn": settings.oracle_dsn,
    }
    if settings.tns_admin:
        # Thin mode admite wallet en versiones actuales de python-oracledb.
        params["config_dir"] = settings.tns_admin
        params["wallet_location"] = settings.tns_admin
        if settings.wallet_password:
            params["wallet_password"] = settings.wallet_password
    return oracledb.connect(**params)
