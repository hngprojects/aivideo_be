from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from fpdf import FPDF
import os
from api.db.database import get_db
from api.v1.models.project import Project
from api.utils.success_response import success_response

save_summary = APIRouter(prefix="/projects", tags=["Projects"])

@save_summary.post("/{project_id}/save-summary", status_code=status.HTTP_201_CREATED)
async def save_summary_as_pdf(project_id: str, db: Session = Depends(get_db)):
    # Validate project ID
    project = db.query(Project).filter(Project.id == project_id, Project.is_deleted == False).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Fetch the summary from the project
    if not project.result or not project.result.strip():
        raise HTTPException(status_code=400, detail="No summary available for this project")
    
    summary_text = project.result
    
    # Generate PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, summary_text)
    
    # Define the file path
    pdf_file_name = f"project_{project_id}_summary.pdf"
    pdf_file_path = os.path.join("pdf_summaries", pdf_file_name)
    
    # Save the PDF to the file system
    os.makedirs(os.path.dirname(pdf_file_path), exist_ok=True)
    pdf.output(pdf_file_path)
    
    # Associate the PDF with the project
    project.file_url = pdf_file_path
    db.commit()

    return success_response(
        status_code=201,
        message="Summary saved as PDF successfully",
        data={
            "pdf_file_path": pdf_file_path,
        }
    )
