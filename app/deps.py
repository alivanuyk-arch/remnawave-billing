from app.remnawave_client import RemnawaveClient

async def get_remnawave_client():
    """Dependency для получения клиента Remnawave"""
    client = RemnawaveClient()
    return client