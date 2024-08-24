from sqlalchemy.orm import Session
from sqlalchemy.exc import NoResultFound

from api.v1.models.usage_store import UserUsageStore

class UserUsageStoreService:
    
    def fetch_by_user(self, db: Session, user_id: str) -> UserUsageStore | None:     
        usage = db.query(UserUsageStore).filter_by(user_id=user_id).first()
        return usage
    
    def get_tools_usage_by_id(self, db: Session, id: int):
        try:
            return db.query(UserUsageStore).filter(UserUsageStore.id == id).one()
        except NoResultFound:
            return None

    def update_tool_usage(self, db: Session, id: int, tool_name: str, value: int):
        tools_usage = self.get_tools_usage_by_id(db, id)
        if tools_usage is None:
            raise ValueError("ToolsUsage record not found")

        # Update the dictionary
        tools = tools_usage.tools_accessed.copy()
        tools[tool_name] = value        
        tools_usage.tools_accessed = tools
        db.add(tools_usage)
        db.commit()
        return tools_usage


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
            raise ValueError("ToolsUsage record not found")

        # Retrieve the tool value from the dictionary
        tools = tools_usage.tools_accessed
        return tools.get(tool_name, None)
    
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
        tools = tools_usage.tools_accessed

        # Check if the tool exists in the dictionary
        if tool_name in tools:
            value = tools[tool_name]
        else:
            # Tool does not exist, create it with a default value of 0
            tools[tool_name] = 0
            value = 0

        # Update the record and commit changes
        tools_usage.tools_accessed = tools
        db.commit()

        return value


user_usage_store_service = UserUsageStoreService()