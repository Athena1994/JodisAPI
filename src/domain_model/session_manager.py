
    def get_job_session(self,
                        session: Session,
                        id: int,
                        raise_: bool) -> JobSession:
        s = session.execute(
                select(JobSession).where(JobSession.id == id)
            ).scalar()
        if raise_ and s is None:
            raise self.IndexValueError(f'No session with id {id} found!')

        return s

    def add_epoch(self,
                  session: JobSession,
                  start: datetime, end: datetime,
                  result: dict):
        session.epochs.append(
            Epoch(
                start_timestamp=start,
                end_timestamp=end,
                result=result
            )
        )