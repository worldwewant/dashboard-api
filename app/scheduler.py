"""
Scheduler contains a task that runs every 12th hour
"""

import logging

from fastapi.concurrency import run_in_threadpool
from rocketry import Rocketry
from rocketry.conds import cron

from app.logginglib import init_custom_logger
from app.utils import data_loader

app = Rocketry(executation="async")

logger = logging.getLogger(__name__)
init_custom_logger(logger)


@app.task(cron("0 */12 * * *"))
async def do_every_12th_hour():
    """
    Load data from BigQuery
    Load coordinates

    Runs at minute 0 past every 12th hour
    """

    try:
        await run_in_threadpool(data_loader.load_data)
        await run_in_threadpool(data_loader.load_coordinates)
    except (Exception,) as e:
        logger.error(f"Error while trying to load data: {str(e)}")