import asyncio
import logging

from app.workers.notification_worker import (
    process_notification_queue,
)

logger = logging.getLogger(__name__)


async def notification_worker_loop(
    stop_event: asyncio.Event,
    poll_interval_seconds: int = 15,
):
    logger.info("SNATCH Notification Worker started.")

    while not stop_event.is_set():

        try:
            result = await asyncio.to_thread(
                process_notification_queue
            )

            if result["processed_count"] > 0:
                logger.info(
                    "Notification worker processed %s records.",
                    result["processed_count"],
                )

        except Exception:
            logger.exception(
                "Notification worker encountered an error."
            )

        try:
            await asyncio.wait_for(
                stop_event.wait(),
                timeout=poll_interval_seconds,
            )
        except asyncio.TimeoutError:
            pass

    logger.info("SNATCH Notification Worker stopped.")