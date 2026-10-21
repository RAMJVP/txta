class VisitorQuestionRepository:
    def __init__(self,db): self.c=db.visitor_questions if db is not None else None
    async def log(self,doc):
        if self.c is not None: await self.c.insert_one(doc)
