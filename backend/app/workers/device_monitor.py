import asyncio
import logging

from app.services.device_service import mark_stale_devices_offline

logger = logging.getLogger(__name__)


async def device_monitor_loop():
    while True:
        try:
            count = await asyncio.to_thread(
                mark_stale_devices_offline,
                5
            )

            if count > 0:
                logger.info(
                    "Marked %s stale devices as offline",
                    count
                )

        except Exception:
            logger.exception("Device monitoring cycle failed")

        await asyncio.sleep(60)