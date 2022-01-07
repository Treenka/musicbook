from sqlalchemy.sql.schema import ForeignKey
import config
from flask import Flask, render_template, request
from flask import flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_migrate import Migrate, current
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

#app = Flask(__name__)
#moment = Moment(app)
# app.config.from_object('config')
#db = SQLAlchemy(app)
db = SQLAlchemy()

# connect to a local postgresql database
#app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=True)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref='venue',
                            lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'Venue ID: {self.id}, Venue Name: {self.name}'

    def __str__(self):
        return f'Venue - {self.name} ({self.id}): {self.city}, {self.state}'

    # implement any missing fields, as a database migration using Flask-Migrate


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=True)
    seeking_description = db.Column(db.String(250))
    shows = db.relationship('Show', backref=db.backref('artist', lazy=True))

    def __repr__(self):
        return f'Artist ID: {self.id}, Artist Name: {self.name}'

    def __str__(self):
        return f'Artist - {self.name} ({self.id}): {self.city}, {self.state}'


class Show (db.Model):
    __tablename__ = 'shows'
    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, ForeignKey(Venue.id))
    artist_id = db.Column(db.Integer, ForeignKey(Artist.id))
    start_time = db.Column(db.DateTime, nullable=False)

    def __repr__(self) -> str:
        return (
            f'Show ID: {self.id}, \n'
            f'Venue: {self.venue.name} ({self.venue.id}), \n'
            f'Artist: {self.artist.name} ({self.artist.id})\n'
        )

    def __str__(self) -> str:
        return (
            f'Artist {self.artist.name} performing at \n'
            f'{self.venue.name} in {self.venue.city}, \n'
            f'{self.venue.state}'
        )


class Genre(db.Model):
    __tablename__ = 'genres'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    artists = db.relationship(
        'Artist', secondary="artist_genres", backref='genres', lazy=True)
    venues = db.relationship(
        'Venue', secondary="venue_genres", backref='genres', lazy=True)

    def __repr__(self):
        return f'Genre ID: {self.id}, Genre Name: {self.name}'

    def __str__(self):
        return f'{self.name}'


venue_genre = db.Table('venue_genres',
                       db.Column('genre_id', db.Integer,
                                 ForeignKey('genres.id')),
                       db.Column('venue_id', db.Integer,
                                 ForeignKey('Venue.id')))

artist_genre = db.Table('artist_genres',
                        db.Column('genre_id', db.Integer,
                                  ForeignKey('genres.id')),
                        db.Column('artist_id', db.Integer,
                                  ForeignKey('Artist.id')))
