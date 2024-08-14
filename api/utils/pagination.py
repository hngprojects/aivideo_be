from typing import Any, Dict, List, Optional
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session, subqueryload
from sqlalchemy import or_
from api.db.database import Base

from api.utils.success_response import success_response


def paginated_response(
    db: Session,
    model,
    skip: int,
    limit: int,
    join: Optional[Any] = None,
    filters: Optional[Dict[str, Any]] = None,
    related_models: Optional[List[Any]] = None,
    related_model_excludes: Optional[Dict[str, List[str]]] = {},
    search: Optional[Dict[str, Any]] = None,
):
    """
    Custom response for pagination.\n
    This takes in four atguments:
        * db- this is the database session
        * model- this is the database table model eg Product, Organisation```
        * limit- this is the number of items to fetch per page, this would be a query parameter
        * skip- this is the number of items to skip before fetching the next page of data. This would also
        be a query parameter
        * join- this is an optional argument to join a table to the query
        * filters- this is an optional dictionary of filters to apply to the query

    Example use:
        **Without filter**
        ``` python
        return paginated_response(
            db=db,
            model=Product,
            limit=limit,
            skip=skip
        )
        ```

        **With filter**
        ``` python
        return paginated_response(
            db=db,
            model=Product,
            limit=limit,
            skip=skip,
            filters={'org_id': org_id}
        )
        ```

        **With join**
        ``` python
        return paginated_response(
            db=db,
            model=Product,
            limit=limit,
            skip=skip,
            join=user_organisation_association,
            filters={'org_id': org_id}
        )
        ```
    """

    query = db.query(model)

    if related_models:
        for related_model in related_models:
            query = query.options(subqueryload(related_model))

    if join is not None:
        query = query.join(join)

    if filters and join is None:
        # Apply filters
        for attr, value in filters.items():
            if value is not None:
                query = query.filter(getattr(model, attr).like(f"%{value}%"))

    elif filters and join is not None:
        # Apply filters
        for attr, value in filters.items():
            if value is not None:
                query = query.filter(
                    getattr(getattr(join, "columns"), attr).like(f"%{value}%")
                )

    if search:
        or_conditions = []
        for attr, value in search.items():
            if value is not None:
                if join and hasattr(join, attr):
                    or_conditions.append(getattr(join, attr).icontains(f"%{value}%"))
                elif hasattr(model, attr):
                    or_conditions.append(getattr(model, attr).icontains(f"%{value}%"))
                else:
                    raise AttributeError(
                        f"'{model.__name__}' or joined model has no attribute '{attr}'"
                    )

        if or_conditions:
            query = query.filter(or_(*or_conditions))

    total = query.count()
    results = jsonable_encoder(query.offset(skip).limit(limit).all())
    total_pages = int(total / limit) + (total % limit > 0)

    items = jsonable_encoder(results)

    if not related_model_excludes.get("user"):
        related_model_excludes["user"] = [
            "password",
            "is_superadmin",
            "is_deleted",
            "is_active",
        ]

    if related_model_excludes:
        for item in items:
            for related_key, fields in related_model_excludes.items():
                related_data = item.get(related_key, {})
                for field in fields:
                    related_data.pop(field, None)

    return success_response(
        status_code=200,
        message="Successfully fetched items",
        data={
            "pages": total_pages,
            "total": total,
            "skip": skip,
            "limit": limit,
            "items": items,
        },
    )
