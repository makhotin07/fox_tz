from fastapi import Query


async def pagination(
    page_size: int | None = Query(50, alias="page[size]"),
    page_number: int | None = Query(1, alias="page[number]"),
):
    return {"page_size": page_size, "page_number": page_number}
