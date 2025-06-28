from typing import Annotated, Union
from uuid import UUID

from asyncpg import Connection
from cms.auth.dependency import (
    RequiresPermission,
)
from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
)
from cms.batch.exceptions import (
    BatchAlreadyExistsException,
    BatchNotFoundException,
)
from cms.batch.models import (
    Batch,
    BatchAlreadyExistsExceptionResponse,
    BatchNotFoundExceptionResponse,
    CreateBatchRequest,
    CreateBatchResponse,
    GetBatchRequest,
    ListBatchResponse,
    UpdateBatchRequest,
)
from cms.batch.repository import BatchRepository
from cms.programs.exceptions import ProgramNotFoundException
from cms.programs.models import ProgramNotFoundExceptionResponse
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

__all__ = [
    "router",
    "create_batch",
    "get_batches",
    "get_batch_by_id",
    "update_batch",
    "delete_batch",
]

router = APIRouter(
    prefix="/batch",
    tags=["batch"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": CredentialsNotFoundExceptionResponse,
            "description": "Credentials not found or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": NotAuthorizedExceptionResponse,
            "description": "User is not authorized to perform this action.",
        },
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequiresPermission("batch:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateBatchResponse,
            "description": "Batch created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": BatchAlreadyExistsExceptionResponse,
            "description": "Batch with the given detail already exists.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ProgramNotFoundExceptionResponse,
            "description": "Program not found.",
        },
    },
)
async def create_batch(
    body: Annotated[CreateBatchRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        batch_id = await BatchRepository.create(
            connection,
            code=body.code,
            program_id=body.program_id,
            name=body.name,
            year=body.year,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateBatchResponse(id=batch_id)
    except BatchAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return BatchAlreadyExistsExceptionResponse(context=e.context)
    except ProgramNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ProgramNotFoundExceptionResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(RequiresPermission("batch:read"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListBatchResponse,
            "description": "List of batches",
        },
    },
)
async def get_batches(
    params: Annotated[GetBatchRequest, Query()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if params.program_id and params.year:
        records = await BatchRepository.get_by_year_program_id(
            connection, params.program_id, params.year
        )
    elif params.program_id:
        records = await BatchRepository.get_by_program_id(
            connection, params.program_id, params.limit, params.offset
        )
    elif params.year:
        records = await BatchRepository.get_by_year(connection, params.year)
    else:
        records = await BatchRepository.get_all(connection, params.limit, params.offset)
    response.status_code = status.HTTP_200_OK
    return ListBatchResponse(
        batches=[
            Batch(
                id=record["id"],
                code=record["code"],
                program_id=record["program_id"],
                program_name=record["program_name"],
                name=record["name"],
                year=record["year"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )


@router.get(
    "/{batch}",
    dependencies=[Depends(RequiresPermission("batch:read"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Batch,
            "description": "Batch details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": BatchNotFoundExceptionResponse,
            "description": "Batch not found.",
        },
    },
)
async def get_batch_by_id(
    batch: Annotated[str, Path(description="Batch ID or Batch Code")],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    param_type = None
    try:
        batch_id = UUID(batch)
        param_type = "id"
    except ValueError:
        # If the batch is not a valid UUID, treat it as a code
        param_type = "code"
    try:
        if param_type == "id":
            record = await BatchRepository.get_by_id(connection, batch_id)
        else:
            record = await BatchRepository.get_by_code(connection, batch)
        response.status_code = status.HTTP_200_OK
        return Batch(
            id=record["id"],
            code=record["code"],
            program_id=record["program_id"],
            program_name=record["program_name"],
            name=record["name"],
            year=record["year"],
            extra_info=record["extra_info"],
        )
    except BatchNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BatchNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequiresPermission("batch:update"))],
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Batch updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                BatchNotFoundExceptionResponse,
                ProgramNotFoundExceptionResponse,
            ],
            "description": "Batch or Program not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": BatchAlreadyExistsExceptionResponse,
            "description": "Batch with the given detail already exists.",
        },
    },
)
async def update_batch(
    batch_id: Annotated[UUID, Path()],
    body: Annotated[UpdateBatchRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await BatchRepository.update(
            connection,
            batch_id,
            code=body.code,
            program_id=body.program_id,
            name=body.name,
            year=body.year,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
    except BatchNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BatchNotFoundExceptionResponse(context=e.context)
    except BatchAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return BatchAlreadyExistsExceptionResponse(context=e.context)
    except ProgramNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ProgramNotFoundExceptionResponse(context=e.context)


@router.delete(
    "/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequiresPermission("batch:delete"))],
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Batch deleted successfully.",
        },
    },
)
async def delete_batch(
    batch_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await BatchRepository.delete(connection, batch_id)
    response.status_code = status.HTTP_204_NO_CONTENT
