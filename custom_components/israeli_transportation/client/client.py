import asyncio

import hishel
from loguru import logger

from .models.bus_response import BusResponse
from .utils import encrypt_key


class Client:
    hishel_client = hishel.AsyncCacheClient(
        base_url="https://silent-be.onrender.com",
        headers={
            "key": encrypt_key(),
            "User-Agent": "israel-transport-homeassistant",
        },
        storage=hishel.AsyncFileStorage(ttl=60),
    )

    @classmethod
    async def get_bus_data(cls, station: str, lines: list[str | int]) -> BusResponse:
        logger.debug(f"Getting info for {station=}, {lines=}")
        try:
            response = await cls.hishel_client.get(
                "busv2",
                extensions={"force_cache": True},
                params={"station": station, "lines": ",".join(map(str, lines))},
            )
            logger.info(f"{response.extensions["from_cache"]=}")
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


if __name__ == "__main__":

    async def debug():
        logger.debug(await Client.get_bus_data(43117, [1, 200]))

    asyncio.run(debug())
