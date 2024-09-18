import json
from db_context import DBContext

with open('sql_test_cfg.json', 'r') as f:
    cfg = DBContext.Config.from_dict(json.load(f))

s = DBContext(cfg)

s.create_tables()
s.add_job({'test': 'test'}, 'test_job', 'Test job to assure everything is '
                                        'working')
s.add_job({'test': 'test2'}, 'job1', 'bar')
s.add_job({'test': 'test2'}, 'job2', 'bar1')
s.add_job({'test': 'test2'}, 'job3', 'bar2')
s.add_job({'test': 'test2'}, 'job4', 'bar2')
s.add_job({'test': 'test2'}, 'job5', 'bar2')
s.add_client('test_client_1')
s.add_client('test_client_2')
s.add_client('test_client_3')

with s.create_session() as session:
    s.assign_job(session, job_id=1, client_id=1)
    s.assign_job(session, job_id=3, client_id=1)
    s.assign_job(session, job_id=4, client_id=2)
    session.commit()
