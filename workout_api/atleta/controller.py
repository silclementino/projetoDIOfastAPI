from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Body, HTTPException, status
from pydantic import UUID4
from sqlalchemy.future import select

from workout_api.atleta.models import AtletaModel
from workout_api.atleta.schemas import AtletaIn, AtletaOut, AtletaResponse, AtletaUpdate
from workout_api.categorias.models import CategoriaModel
from workout_api.centro_treinamento.models import CentroTreinamentoModel
from workout_api.contrib.dependencies import DatabaseDependency

from sqlalchemy.exc import IntegrityError

#Add pagination with SQLAlchemy
from fastapi_pagination import LimitOffsetPage, Page
from fastapi_pagination.ext.sqlalchemy import paginate

router = APIRouter()

@router.post(
        path='/', 
        summary='Criar um novo atleta',
        status_code = status.HTTP_201_CREATED,
        response_model=AtletaOut
        ) 


async def post(
    db_session: DatabaseDependency, 
    atleta_in: AtletaIn = Body(...)):
    """
    cpf_atleta = atleta_in.cpf
    cpf = (await db_session.execute(select(
        AtletaModel).filter_by(cpf=cpf_atleta))).scalars().first()
    
    if cpf:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f'Já existe um atleta cadastrado com o cpf: {cpf_atleta}'
        )
    """
    categoria_name = atleta_in.categoria.nome
    categoria = (await db_session.execute(select(
        CategoriaModel).filter_by(nome=categoria_name))).scalars().first()

    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'A categoria {categoria_name} não foi encontrada.'
        )        

    centro_treinamento_name = atleta_in.centro_treinamento.nome
    centro_treinamento = (await db_session.execute(select(
        CentroTreinamentoModel).filter_by(nome=centro_treinamento_name))).scalars().first()

    if not centro_treinamento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'O centro de treinamento {centro_treinamento_name} não foi encontrada.'
        )        
    try:
        atleta_out = AtletaOut(id=uuid4(), created_at=datetime.utcnow(), **atleta_in.model_dump())
        atleta_model = AtletaModel(**atleta_out.model_dump(exclude={'categoria', 'centro_treinamento'}))

        atleta_model.categoria_id = categoria.pk_id
        atleta_model.centro_treinamento_id = centro_treinamento.pk_id

        db_session.add(atleta_model)
        await db_session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail=f'Já existe um atleta cadastrado com o cpf: {atleta_in.cpf}'
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail='Ocorreu um erro ao inserir os dado no banco.'
        )  
    return atleta_out

@router.get(
        path='/', 
        summary='consultar todos os atletas',
        status_code = status.HTTP_200_OK,
        response_model= LimitOffsetPage[AtletaOut],
        ) 


async def query(db_session: DatabaseDependency):
    
    return await paginate(db_session, select(AtletaModel))

"""
@router.get(
        path='/', 
        summary='consultar todos os atletas',
        status_code = status.HTTP_200_OK,
        response_model= list[AtletaOut],
        ) 


async def query(db_session: DatabaseDependency) -> list[AtletaOut]:
    atletas: list[AtletaOut] = (await db_session.execute(select(AtletaModel))).scalars().all()
    
    return [AtletaOut.model_validate(atleta) for atleta in atletas]
"""
@router.get(
        path='/all_atletas', 
        summary='consulta personalizada todos os atletas',
        status_code = status.HTTP_200_OK,
        response_model= list[AtletaResponse],
        ) 


async def query(db_session: DatabaseDependency) -> list[AtletaResponse]:
    atletas: list[AtletaResponse] = (await db_session.execute(select(AtletaModel))).scalars().all()

    return [AtletaResponse.model_validate(atleta) for atleta in atletas]

@router.get(
        path='/nome={nome}', 
        summary='consultar um atleta pelo nome',
        status_code = status.HTTP_200_OK,
        response_model= AtletaOut,
        ) 


async def query(nome: str, db_session: DatabaseDependency, cpf: str | None = None) -> AtletaOut:
    atleta: AtletaOut = (
    await db_session.execute(select(AtletaModel).filter_by(nome=nome, cpf=cpf))
        ).scalars().first()
     
    if not atleta:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail= f'Atleta não encontrado com nome: {nome}'
            )
    
    return atleta

@router.get(
        path='/{id}', 
        summary='consultar um atleta pelo id',
        status_code = status.HTTP_200_OK,
        response_model= AtletaOut,
        ) 

async def query(id: UUID4, db_session: DatabaseDependency) -> AtletaOut:
    atleta: AtletaOut = (
    await db_session.execute(select(AtletaModel).filter_by(id=id))
        ).scalars().first()
     
    if not atleta:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail= f'Atleta não encontrada no id: {id}'
            )
    
    return atleta


@router.patch(
        path='/{id}', 
        summary='Editar um atleta pelo id',
        status_code = status.HTTP_200_OK,
        response_model= AtletaOut,
        ) 


async def query(id: UUID4, db_session: DatabaseDependency, atleta_up: AtletaUpdate = Body(...)) -> AtletaOut:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
        ).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail= f'Atleta não encontrada no id: {id}'
            )
    
    atleta_update = atleta_up.model_dump(exclude_unset=True)
    for key, value in atleta_update.items():
        setattr(atleta, key, value)
    
    await db_session.commit()
    await db_session.refresh(atleta)

    return atleta


@router.delete(
        path='/{id}', 
        summary='Deletar um atleta pelo id',
        status_code = status.HTTP_204_NO_CONTENT,
        ) 


async def query(id: UUID4, db_session: DatabaseDependency) -> None:
    atleta: AtletaOut = (
        await db_session.execute(select(AtletaModel).filter_by(id=id))
        ).scalars().first()
    
    if not atleta:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND, 
            detail= f'Atleta não encontrada no id: {id}'
            )
    
    await db_session.delete(atleta)
    await db_session.commit()


