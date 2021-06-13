from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from . import models


class Database:
    def __init__(self, db_url: str):
        engine = create_engine(db_url)
        models.Base.metadata.create_all(bind=engine)
        self.maker = sessionmaker(bind=engine)

    def get_or_create(self, session, model, filter_field, data):
        instance = (
            session.query(model)
            .filter_by(**{filter_field: data[filter_field]})
            .first()
        )
        if not instance:
            instance = model(**data)
        return instance

    def add_post(self, data):
        session = self.maker()
        post = self.get_or_create(
            session, models.Post, "id", data["post_data"]
        )
        author = self.get_or_create(
            session, models.Author, "url", data["author_data"]
        )
        post.author = author
        for tag_data in data["tags_data"]:
            tag = self.get_or_create(session, models.Tag, "name", tag_data)
            post.tag.append(tag)
        session.add(post)
        previous_comment = None
        for comment_data in data["comments_data"]:
            comment_data["post_id"] = post.id
            comment = self.get_or_create(
                session, models.Comment, "id", comment_data
            )
            if previous_comment is not None:
                previous_comment.next_comment_id = comment.id
                session.add(previous_comment)
            previous_comment = comment
        if previous_comment is not None:
            session.add(previous_comment)
        try:
            session.commit()
        except Exception:
            session.rollback()
        finally:
            session.close()
