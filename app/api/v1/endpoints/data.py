import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, status

from app.api import dependencies
from app.logginglib import init_custom_logger
from app.schemas.data_is_loading import DataIsLoading
from app.schemas.parameters_user import ParametersUser
from app.utils import data_loader
from app import global_variables

logger = logging.getLogger(__name__)
init_custom_logger(logger)

router = APIRouter(prefix="/data")


@router.get(
    path="/loading-status",
    response_model=DataIsLoading,
    status_code=status.HTTP_200_OK,
)
def read_data_loading_status(
    _: Annotated[ParametersUser, Depends(dependencies.dep_parameters_user)]
):
    """Check if data is loading"""

    return DataIsLoading(is_loading=global_variables.is_loading_data)


@router.post(
    path="/reload",
    status_code=status.HTTP_202_ACCEPTED,
)
def init_data_reloading(
    _: Annotated[ParametersUser, Depends(dependencies.dep_parameters_user_admin)],
    background_tasks: BackgroundTasks,
):
    """Init data reloading"""

    if not global_variables.is_loading_data:
        try:
            background_tasks.add_task(data_loader.reload_data, True, True)
        except (Exception,) as e:
            logger.error(f"An error occurred while reloading data: {str(e)}")