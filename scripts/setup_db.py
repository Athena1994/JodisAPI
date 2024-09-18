import json
from db_context import DBContext

with open('program/server/sql_cfg.json', 'r') as f:
    cfg = DBContext.Config.from_dict(json.load(f))

s = DBContext(cfg)

s.create_tables()
