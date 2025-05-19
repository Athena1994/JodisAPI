

from dataclasses import dataclass

from sqlalchemy.types import TypeDecorator, JSON


@dataclass
class JobData:
    module_id: str
    payload_key: str
    cfg: dict

    class Type(TypeDecorator):
        """Custom SQLAlchemy type for storing JobData as JSON."""
        impl = JSON

        def process_bind_param(self, value, dialect):
            """Serialize JobData to JSON when saving to the database."""
            if value is None:
                return None
            # print("JobData TypeDecorator: ", value, type(value))
            if isinstance(value, JobData):
                return value.__dict__

            raise ValueError("Invalid type for JobDataType")

        def process_result_value(self, value, dialect):
            """Deserialize JSON to JobData when loading from the database."""
            if value is None:
                return None
            return JobData(**value)
