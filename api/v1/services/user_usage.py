from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from api.v1.models.usage_store import UserUsageStore, UserToolAccess

class UserUsageStoreService:
    
    def create_tool_access(db: Session, usage_store_id: int, tool_name: str, access_count: int) -> UserToolAccess:
        """
        Creates a new UserToolAccess record in the database.

        :param db: SQLAlchemy session
        :param usage_store_id: The ID of the related UsageStore
        :param tool_name: The name of the tool
        :param access_count: The access count for the tool
        :return: The created UserToolAccess record
        """
        new_tool_access = UserToolAccess(
            tool_name=tool_name,
            access_count=access_count,
            usage_store_id=usage_store_id
        )
        
        try:
            db.add(new_tool_access)
            db.commit()
            db.refresh(new_tool_access)
            return new_tool_access
        except IntegrityError as e:
            db.rollback()
            print(f"Integrity error: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

        except Exception as e:
            db.rollback()
            print(f"An error occurred: {e}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    def fetch_by_user(self, db: Session, user_id: str) -> UserUsageStore | None:     
        usage = db.query(UserUsageStore).filter_by(user_id=user_id).first()
        if not usage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User usage not found")
        return usage    
    
    def fetch_by_id(self, db: Session, id: int):
        usage = db.query(UserUsageStore).filter(UserUsageStore.id == id).one()
        if not usage:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User usage not found")
        return usage

    def update_tool_usage(self, db: Session, id: int, tool_name: str, value: int):
        tools_usage = self.fetch_by_id(db, id)
        if tools_usage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND ,detail="Tool Usage record not found")

        # Update the dictionary
        tool = next((tool for tool in tools_usage.tools if tool.tool_name == tool_name), None)
        tool.access_count = value        
        db.commit()
        return tool

    def get_tool_value(self, db: Session, id: int, tool_name: str):
        """
        Retrieve the value of a specific tool from the tools_accessed dictionary.

        :param db: SQLAlchemy session
        :param id: ID of the ToolsUsage record
        :param tool_name: Name of the tool to retrieve the value for
        :return: Value of the tool if found, otherwise None
        """
        tools_usage = self.get_tools_usage_by_id(db, id)
        if tools_usage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND ,detail="Tool Usage record not found")

        # Retrieve the tool value from the dictionary
        tool = next((tool for tool in tools_usage.tools if tool.tool_name == tool_name), None)
        return tool.access_count
    
    def fetch_total(self, db: Session, id: int) -> int:
        """
        Retrieves the total access count for all tools in the ToolsUsage record with the given ID.

        :param db: SQLAlchemy session object for database operations.
        :param id: ID of the ToolsUsage record to retrieve the total access count for.

        :return: Total access count for all tools in the ToolsUsage record.
        :raises HTTPException: If the ToolsUsage record with the given ID is not found.
        """
        tools_usage = self.get_tools_usage_by_id(db, id)
        if tools_usage is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usage record not found")
        return tools_usage.tool_access_count
    
    def get_or_create_tool_value(self, db: Session, id: int, tool_name: str):
        """
        Retrieve the value of a specific tool from the tools_accessed dictionary.
        If the tool does not exist, it creates it with a value of 0 and returns that value.

        :param db: SQLAlchemy session
        :param id: ID of the ToolsUsage record
        :param tool_name: Name of the tool to retrieve the value for
        :return: Value of the tool
        """
        tools_usage = self.get_tools_usage_by_id(db, id)
        if tools_usage is None:
            raise ValueError("ToolsUsage record not found")

        # Retrieve the dictionary
        tool = [tool.tool_name for tool in tools_usage.tools]

        # Check if the tool exists in the dictionary
        if tool_name in tool:
            value = tool.access_count
        else:
            # Tool does not exist, create it with a default value of 0
            value = self.create_tool_access(
                db,
                id,
                tool_name,
                0
            )

        return value
    
    def add_tool_access_count_by_id(self, db: Session, id:str, value:int):
        tool = self.fetch_by_id(db, id)
        # Increment the access count for the tool
        tool.tool_access_count += value
        db.commit()
        return tool.tool_access_count
    
    def add_tool_access_count_by_user(self, db: Session, user_id:str, value:int):
        tool = self.fetch_by_user(db, user_id)
        tool.tool_access_count += value
        db.commit()
        return tool.tool_access_count

user_usage_store_service = UserUsageStoreService()