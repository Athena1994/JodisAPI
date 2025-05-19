

from abc import abstractmethod

from services.jobs.job_data import JobData


class JobProcessor:

    def __init__(self):
        pass

    @abstractmethod
    def process(self, job: JobData):
        """
        Process the job data.
        :param job: Job data to be processed.
        """
        raise NotImplementedError()
