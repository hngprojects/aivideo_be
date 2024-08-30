
import json
import base64

from api.v1.services.project import project_service
from api.v1.models.project import Project
from sqlalchemy.orm import Session



class TestSetFileUrl:

    # set_file_url successfully generates a file URL and updates the project when a download_url exists
    def test_successful_update_with_download_url(self, mocker):
        mock_db = mocker.Mock(spec=Session)
        project = Project(
            title='Test Title',
            project_type='Youtube Summarizer',
            result=json.dumps({
                'download_url': 'http://example.com/file'
                }))

        project_service.set_file_url(mock_db, project)

        assert project.file_url == 'http://example.com/file'
        mock_db.commit.assert_called_once()


    # set_file_url successfully generates a file URL and updates the project when a download_url exists in a quality dict
    def test_successful_update_with_quality_dict(self, mocker):
        mock_db = mocker.Mock(spec=Session)
        project = Project(
            title='Test Title',
            project_type='Youtube Summarizer',
            result=json.dumps({
            'quality':{
                'high_quality': 'http://example.com/file'
                }
            }))

        project_service.set_file_url(mock_db, project)

        assert project.file_url == 'http://example.com/file'
        mock_db.commit.assert_called_once()


    # set_file_url successfully generates a file URL and updates the project when a summary exists
    def test_successful_update_with_summary(self, mocker):
        mock_db = mocker.Mock(spec=Session)

        summary_text = 'This is a very short textual summary'
        project = Project(
            title='Test Title',
            project_type='Youtube Summarizer',
            result=json.dumps({
                'summary': summary_text
                }))

        project_service.set_file_url(mock_db, project)

        mime = 'text/plain'
        prefix = f'data:{mime};base64,'
        
        b64_enc = base64.b64encode(bytes(summary_text, 'utf-8')).decode('utf-8')


        assert project.file_url == f'{prefix}{b64_enc}'
        mock_db.commit.assert_called_once()



    # set_file_url handles projects with empty result data
    def test_set_file_url_empty_result(self, mocker):

        mock_db = mocker.Mock(spec=Session)
        project = Project(
            title='Test Title',
            project_type='Youtube Summarizer',
            result=None
            )

        project_service.set_file_url(mock_db, project)

        assert project.file_url is None
        mock_db.commit.assert_not_called()

    # set_file_url handles projects with malformed JSON in result data
    def test_set_file_url_malformed_json(self, mocker):
        mock_db = mocker.Mock(spec=Session)
        project = Project(result='{"download_url: "http://example.com/file"')

        project_service.set_file_url(mock_db, project)

        assert project.file_url is None
        mock_db.commit.assert_not_called()

    # set_file_url handles projects with missing download_url, quality, and summary keys
    def test_set_file_url_missing_keys(self, mocker):
        mock_db = mocker.Mock(spec=Session)
        project = Project(result=json.dumps({}))

        project_service.set_file_url(mock_db, project)

        assert project.file_url is None
        mock_db.commit.assert_not_called()