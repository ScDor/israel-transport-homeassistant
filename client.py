import httpx

from models.bus_response import BusResponse
from utils import encrypt_key
from loguru import logger


class Client:
    httpx_client = httpx.AsyncClient(
        base_url="https://silent-be.onrender.com",
        headers={
            "key": encrypt_key(),
            "User-Agent": "israel-transport-homeassistant",
        },
    )

    @classmethod
    async def get_bus_data(cls, station: str, lines: list[int]) -> BusResponse:
        logger.debug(f"Getting info for {station=}, {lines=}")
        try:
            response = await cls.httpx_client.get(
                "busv2",
                params={
                    "station": station,
                    "lines": ",".join(map(str, lines)),
                },
            )
            response.raise_for_status()
        except Exception:
            logger.exception("Failed getting API data")
            raise

        try:
            result = BusResponse.model_validate_json(response.content)
        except Exception:
            logger.exception(
                f"Failed parsing response: {response.status_code=}, {response.content=}"
            )
            raise

        logger.debug(result)
        return result
