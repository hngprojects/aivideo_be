import base64
import json

from api.v1.models import Project
from api.utils import mime_types


def make_data_uri(content: bytes, mime=mime_types.TEXT_PLAIN):
    prefix = f'data:{mime};base64,'

    b64_enc = base64.b64encode(content).decode('utf-8')
    uri = f'{prefix}{b64_enc}'

    return uri


def generate_file_url(project: Project):
    """This function extracts a download url from the results stored in the given project if present else generate a download data uri.

    Args:
        project (Project)
    """
    if project.result is None:
        return None
    
    result_dict = json.loads(project.result)
    if result_dict.get('download_url') is not None:
        return result_dict['download_url']
    elif result_dict.get('quality') is not None:
        return result_dict.get('quality', {}).get('high_quality')
    elif result_dict.get('summary') is not None:
        data_uri = make_data_uri(bytes(result_dict['summary'], 'utf-8'))

        return data_uri

    else:
        return None