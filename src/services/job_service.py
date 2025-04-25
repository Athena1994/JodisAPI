

class JobService:
    def __init__(self, job_repository):
        self.job_repository = job_repository

    def get_job_by_id(self, job_id):
        return self.job_repository.get_job_by_id(job_id)

    def create_job(self, job_data):
        return self.job_repository.create_job(job_data)

    def update_job(self, job_id, job_data):
        return self.job_repository.update_job(job_id, job_data)

    def delete_job(self, job_id):
        return self.job_repository.delete_job(job_id)