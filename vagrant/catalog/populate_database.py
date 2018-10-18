from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User

engine = create_engine('sqlite:///itemcatalogwithusers.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


User1 = User(name='Default',
             email='Default')
session.add(User1)
session.commit()

category1 = Category(name='Soccer')
session.add(category1)
session.commit()

item1 = Item(name='Soccer Cleats',
             category=category1,
             user_id=1)
session.add(item1)
session.commit()

item2 = Item(name='Jersey',
             category=category1,
             user_id=1)
session.add(item2)
session.commit()

item3 = Item(name='Shin Guards',
             category=category1,
             user_id=1)
session.add(item3)
session.commit()

category2 = Category(name='Baseball')
session.add(category2)
session.commit()

item1 = Item(name='Bat',
             category=category2,
             user_id=1)
session.add(item1)
session.commit()

item2 = Item(name='Batter\'s Helmet',
             category=category2,
             user_id=1)
session.add(item2)
session.commit()

item3 = Item(name='Baseball Mitt',
             category=category2,
             user_id=1)
session.add(item3)
session.commit()

category3 = Category(name='Football')
session.add(category3)
session.commit()

item1 = Item(name='Face Mask',
             category=category3,
             user_id=1)
session.add(item1)
session.commit()

item2 = Item(name='Girdle',
             category=category3,
             user_id=1)
session.add(item2)
session.commit()

item3 = Item(name='Mouth Guard',
             category=category3,
             user_id=1)
session.add(item3)
session.commit()

category4 = Category(name='Basketball')
session.add(category4)
session.commit()

category5 = Category(name='Frisbee')
session.add(category5)
session.commit()

category6 = Category(name='Snowboarding')
session.add(category6)
session.commit()

category7 = Category(name='Rock Climbing')
session.add(category7)
session.commit()

category8 = Category(name='Skating')
session.add(category8)
session.commit()

category9 = Category(name='Hockey')
session.add(category9)
session.commit()

print("populated database!")