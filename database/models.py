from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship

from sqlalchemy import (
    Table, Column, Integer, String, ForeignKey
)


Base = declarative_base()


tag_association = Table("tag_to_post", Base.metadata,
    Column("tag_id", Integer, ForeignKey("tag.id")),
    Column("post_id", Integer, ForeignKey("post.id"))
)


class Post(Base):
    __tablename__ = "post"
    id = Column(Integer, primary_key=True, nullable=False, unique=True)
    url = Column(String(2048), nullable=False, unique=True)
    title = Column(String, nullable=False, unique=False)
    author_id = Column(Integer, ForeignKey("author.id"), nullable=False)
    author = relationship("Author", backref="posts")
    tag = relationship("Tag",
                            secondary=tag_association,
                            backref="posts")


class Author(Base):
    __tablename__ = "author"
    id = Column(Integer, primary_key=True, nullable=False, unique=True, autoincrement=True)
    url = Column(String(2048), nullable=False, unique=True)
    name = Column(String(250), nullable=False, unique=False)


class Comment(Base):
    __tablename__ = "comment"
    id = Column(Integer, primary_key=True)
    next_comment_id = Column(Integer, ForeignKey("comment.id"), nullable=True)
    post_id = Column(Integer, ForeignKey("post.id"), nullable=False)
    body = Column(String, nullable=False)
    comment_author_url = Column(String, nullable=False)


class Tag(Base):
    __tablename__ = "tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True)
    url = Column(String, nullable=False, unique=True)
