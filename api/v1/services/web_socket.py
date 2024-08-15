class WebsocketService:

    async def send_job_status_updates(self, websocket: WebSocket, job_id: str):
        """Function to send job status over websockets"""

        while True:
            task_result = AsyncResult(job_id, app=worker)
            project = job_service.get_project_from_job(job_id=job_id)

            status = task_result.state
            result = None

            # Send WebSocket message with current status
            await manager.send_message(
                message=f"Job {job_id}: Status is {status}",
                websocket=websocket
            )

            if status == 'PENDING':
                job_service.update_job(job_id, 'PENDING')

            elif status == 'FAILURE':
                result = str(task_result.info)
                job_service.update_job(job_id, 'FAILURE', result)

                await manager.send_message(
                    message=f"Job {job_id} failed with error: {result}",
                    websocket=websocket
                )
                break
            
            elif status == 'SUCCESS':
                result = task_result.result
                job_service.update_job(job_id, 'SUCCESS', result)

                project.result = result
                db.commit()

                await manager.send_message(
                    message=f"Job {job_id} completed successfully.",
                    websocket=websocket
                )
                break
                
            else:
                job_service.update_job(job_id, status)
