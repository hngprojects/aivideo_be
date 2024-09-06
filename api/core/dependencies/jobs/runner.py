from api.v1.schemas.project import ProjectToolsEnum as tools


BASE_DIR = 'api/core/dependencies/jobs/tasks'

# Mapping between script names and their corresponding tools
# This is basically to register task scripts
script_to_tool_mapping = {
    tools.talking_avatar.value: f'{BASE_DIR}/talking_avatar.py'
}
