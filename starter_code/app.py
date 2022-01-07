# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import dateutil.parser
import babel
from sqlalchemy.sql.schema import ForeignKey
import config
from flask import Flask, render_template, request
from flask import flash, redirect, url_for, jsonify
from flask_moment import Moment
from flask_migrate import Migrate, current
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from datetime import datetime
from models import db, Venue, Show, Artist, Genre


# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
#db = SQLAlchemy(app)
db.init_app(app)

# connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

migrate = Migrate(app, db)

# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Venues
#  ----------------------------------------------------------------


@app.route('/venues')
def venues():
    # num_upcoming_shows aggregated
    # based on number of upcoming shows per venue.

    # store all venues
    venues = Venue.query.all()

    # store all states that venues are in
    states = list(set([venue.state for venue in venues]))

    # create list for data to be displayed
    new_data = []

    for state in states:
        current_st_venues = Venue.query.filter_by(state=state)
        cities = list(set([venue.city for venue in current_st_venues]))
        for city in cities:
            venue_collection = {}
            venue_collection['state'] = state
            venue_collection['city'] = city
            venue_collection['venues'] = []
            current_city_venues = current_st_venues.filter_by(city=city)
            for venue in current_city_venues:
                venue_arena = {
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': len(
                        list(
                            filter(
                                lambda x: x.start_time > datetime.today(),
                                venue.shows
                            )
                        )
                    )
                }
                venue_collection['venues'].append(venue_arena)
            new_data.append(venue_collection)

    return render_template('pages/venues.html', areas=new_data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    # implement search on artists with
    # partial string search. Ensure it is case-insensitive.
    # seach for Hop should return "The Musical Hop".
    # search for "Music" should return
    # "The Musical Hop" and "Park Square Live Music & Coffee"
    text = request.form.get('search_term', '')

    new_response = {'count': 0, 'data': []}

    for venue in Venue.query.all():
        if text.lower() in venue.name.lower():
            new_response['count'] += 1
            add_data = {
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(
                    list(
                        filter(
                            lambda x: x.start_time > datetime.today(),
                            venue.shows
                        )
                    )
                )
            }
            new_response['data'].append(add_data)

    return render_template(
        'pages/search_venues.html',
        results=new_response,
        search_term=request.form.get('search_term', '')
    )


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # replace with real venue data from the venues table, using venue_id

    new_data = {}
    current_venue = Venue.query.get(venue_id)

    if current_venue:

        new_data['id'] = current_venue.id
        new_data['name'] = current_venue.name
        new_data['genres'] = current_venue.genres
        new_data['address'] = current_venue.address
        new_data['city'] = current_venue.city
        new_data['state'] = current_venue.state
        new_data['phone'] = current_venue.phone
        new_data['website'] = current_venue.website
        new_data['facebook_link'] = current_venue.facebook_link
        new_data['seeking_talent'] = current_venue.seeking_talent
        new_data['seeking_description'] = current_venue.seeking_description
        new_data['image_link'] = current_venue.image_link
        new_data['past_shows'] = []
        new_data['upcoming_shows'] = []
        past_shows = [
            show for show in current_venue.shows
            if show.start_time < datetime.today()
        ]

        if len(past_shows) > 0:
            for show in past_shows:
                show_dict = {
                    'artist_id': show.artist.id,
                    'artist_name': show.artist.name,
                    'artist_image_link': show.artist.image_link,
                    'start_time': str(show.start_time)
                }

                new_data['past_shows'].append(show_dict)

        upcoming_shows = [
            show for show in current_venue.shows
            if show.start_time > datetime.today()
        ]

        if len(upcoming_shows) > 0:
            for show in upcoming_shows:
                show_dict = {
                    'artist_id': show.artist.id,
                    'artist_name': show.artist.name,
                    'artist_image_link': show.artist.image_link,
                    'start_time': str(show.start_time)
                }

                new_data['upcoming_shows'].append(show_dict)

        new_data['past_shows_count'] = len(past_shows)
        new_data['upcoming_shows_count'] = len(upcoming_shows)

        return render_template('pages/show_venue.html', venue=new_data)
    else:

        return render_template('pages/home.html')
#  ----------------------------------------------------------------
#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # insert form data as a new Venue record in the db, instead
    # modify data to be the data object returned from db insertion

    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        address = request.form.get('address')
        phone = request.form.get('phone')
        genres = request.form.getlist('genres')
        facebook_link = request.form.get('facebook_link')
        image_link = request.form.get('image_link')
        website_link = request.form.get('website_link')
        seeking_talent = request.form.get('seeking_talent')
        seeking_description = request.form.get(
            'seeking_description'
        )

        genre_objects = []
        all_genre_names = [
            genre.name for genre in Genre.query.all()
        ]
        for genre in genres:
            if genre in all_genre_names:
                go = Genre.query.filter_by(name=genre).all()[0]
                genre_objects.append(go)
            else:
                new_genre = Genre(name=genre)
                try:
                    db.session.add(new_genre)
                    db.session.commit()
                    new_genre_success = True
                except Exception as e:
                    print(e)
                    db.session.rollback()
                    new_genre_success = False
                finally:
                    if new_genre_success:
                        go = Genre.query.filter_by(name=genre).all()[0]
                        genre_objects.append(go)
                    else:
                        flash('An error occurred. Venue ' +
                              name + ' could not be listed.')
                        return render_template('pages/home.html')
        if seeking_talent == 'y':
            seeking_talent = True
        else:
            seeking_talent = False

        new_venue = Venue(
            name=name,
            city=city,
            state=state,
            address=address,
            phone=phone,
            genres=genre_objects,
            facebook_link=facebook_link,
            website=website_link,
            image_link=image_link,
            seeking_talent=seeking_talent,
            seeking_description=seeking_description

        )

        db.session.add(new_venue)
        db.session.commit()
        success = True
    except Exception as e:
        print(e)
        db.session.rollback()
        success = False
    finally:
        db.session.close()

        if success:
            flash('Venue ' + name + ' was successfully listed!')
            return render_template('pages/home.html')
        else:
            flash('An error occurred. Venue ' + name + ' could not be listed.')
            return render_template('pages/home.html')

    # on successful db insert, flash success
    # on unsuccessful db insert, flash an error instead.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record.
    # Handle cases where the session commit could fail.

    # add an if statement saying that if the venue id
    # does not exist in the db then redirect to index

    # also check if you can cancel the buttons auto response

    if Venue.query.get(venue_id) is None:
        return redirect(url_for('index'))

    delete_response = {}

    try:

        current_venue = Venue.query.get(venue_id)
        print(f'This is the current venue:{current_venue}')
        name = current_venue.name
        db.session.delete(current_venue)
        db.session.commit()
        delete_response['success'] = True
        delete_response['message'] = f'{name} has successfully been deleted.'
    except Exception as e:
        print(e)
        db.session.rollback()
        delete_response['success'] = False
        delete_response['message'] = (
            f'An error has occured.\n'
            f' {name} has not been deleted.'
        )
    finally:
        db.session.close()
        return jsonify(delete_response)
    # BC: Implement a button to delete a
    # Venue on a Venue Page, have it so that
    # clicking that button delete it from
    # the db then redirect the user to the homepage

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # replace with real data returned from querying the database
    artist_data = []

    for artist in Artist.query.all():
        artist_data.append({
            'id': artist.id,
            'name': artist.name})

    return render_template('pages/artists.html', artists=artist_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # implement search on artists with partial
    # string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals",
    # "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".

    # create list to hold the found artists
    search_list = []
    # variable to hold the search term
    text = request.form.get('search_term', '')
    # variable to hold the amount of artists found
    count = 0

    # add the artists that match the search terms
    # to the search_list
    for artist in Artist.query.all():
        if text.lower() in artist.name.lower():
            search_list.append(artist)
            count += 1

    # create variable to hold the data of search objects
    response = {}
    response['count'] = count
    response['data'] = []

    for artist in search_list:
        response['data'].append({
            'id': artist.id,
            'name': artist.name,
            'num_upcoming_shows': len(
                list(
                    filter(
                        lambda x: x.start_time > datetime.today(),
                        artist.shows
                    )
                )
            )
        })

    return render_template(
        'pages/search_artists.html',
        results=response,
        search_term=request.form.get('search_term', '')
    )


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # replace with real artist data from
    # the artist table, using artist_id

    artist = Artist.query.get(artist_id)

    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'image_link': artist.image_link,
        'past_shows': [],
        'upcoming_shows': [],
        'past_show_count': len(
            list(
                filter(
                    lambda x: x.start_time < datetime.today(),
                    artist.shows
                )
            )
        ),
        'upcoming_shows_count': len(
            list(
                filter(
                    lambda x: x.start_time > datetime.today(),
                    artist.shows
                )
            )
        )
    }

    # add past_shows data
    for show in artist.shows:
        if show.start_time < datetime.today():
            data['past_shows'].append(
                {
                    'venue_id': show.venue.id,
                    'venue_name': show.venue.name,
                    'venue_image_link': show.venue.image_link,
                    'start_time': str(show.start_time)
                }
            )
    # add upcoming_shows data
    for show in artist.shows:
        if show.start_time > datetime.today():
            data['upcoming_shows'].append(
                {
                    'venue_id': show.venue.id,
                    'venue_name': show.venue.name,
                    'venue_image_link': show.venue.image_link,
                    'start_time': str(show.start_time)
                }
            )

    return render_template(
        'pages/show_artist.html',
        artist=data
    )

#  ----------------------------------------------------------------
#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()

    artist_to_edit = Artist.query.get(artist_id)

    artist = {
        'id': artist_to_edit.id,
        'name': artist_to_edit.name,
        'genres': artist_to_edit.genres,
        'city': artist_to_edit.city,
        'state': artist_to_edit.state,
        'phone': artist_to_edit.phone,
        'website': artist_to_edit.website,
        'facebook_link': artist_to_edit.facebook_link,
        'seeking_venue': artist_to_edit.seeking_venue,
        'seeking_description': artist_to_edit.seeking_description,
        'image_link': artist_to_edit.image_link
    }

    # populate form with fields from artist with ID < artist_id >
    return render_template(
        'forms/edit_artist.html',
        form=form,
        artist=artist_to_edit
    )


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    artist_to_edit = Artist.query.get(artist_id)
    artist_to_edit.name = request.form.get("name")
    artist_to_edit.city = request.form.get('city')
    artist_to_edit.state = request.form.get('state')
    artist_to_edit.phone = request.form.get('phone')
    artist_to_edit.genres = request.form.getlist('genres')
    artist_to_edit.facebook_link = request.form.get('facebook_link')
    artist_to_edit.image_link = request.form.get('image_link')
    artist_to_edit.website = request.form.get('website_link')
    artist_to_edit.seeking_venue = request.form.get('seeking_venue')
    artist_to_edit.seeking_description = request.form.get(
        'seeking_description'
    )

    return redirect(
        url_for(
            'show_artist',
            artist_id=artist_id
        )
    )


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    venue = Venue.query.get(venue_id)

    # populate form with values from
    # venue with ID <venue_id>
    return render_template(
        'forms/edit_venue.html',
        form=form,
        venue=venue
    )


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form
    # submitted, and update existing
    # venue record with ID <venue_id>
    # using the new attributes

    venue = Venue.query.get(venue_id)
    venue.name = request.form.get('name')
    venue.city = request.form.get('city')
    venue.state = request.form.get('state')
    venue.phone = request.form.get('phone')
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form.get('facebook_link')
    venue.image_link = request.form.get('image_link')
    venue.website = request.form.get('website_link')
    venue.seeking_venue = request.form.get('seeking_venue')
    venue.seeking_description = request.form.get('seeking_description')
    return redirect(url_for('show_venue', venue_id=venue_id))

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # insert form data as a new
    # Venue record in the db, instead
    # modify data to be the data
    # object returned from db insertion

    # Try: insert the form data for a new artist object
    # open the connection, save data to a var if necessary

    try:
        name = request.form.get('name')
        city = request.form.get('city')
        state = request.form.get('state')
        phone = request.form.get('phone')
        genres = request.form.getlist('genres')
        facebook_link = request.form.get('facebook_link')
        image_link = request.form.get('image_link')
        website_link = request.form.get('website_link')
        seeking_talent = request.form.get('seeking_talent')
        seeking_description = request.form.get('seeking_description')

        genre_objects = []
        all_genre_names = [genre.name for genre in Genre.query.all()]
        for genre in genres:
            if genre in all_genre_names:
                go = Genre.query.filter_by(name=genre).all()[0]
                genre_objects.append(go)
            else:
                new_genre = Genre(name=genre)
                try:
                    db.session.add(new_genre)
                    db.session.commit()
                    new_genre_success = True
                except Exception as e:
                    print(e)
                    db.session.rollback()
                    new_genre_success = False
                finally:
                    if new_genre_success:
                        go = Genre.query.filter_by(name=genre).all()[0]
                        genre_objects.append(go)
                    else:
                        flash('An error occurred. Venue ' +
                              name + ' could not be listed.')
                        return render_template('pages/home.html')
        if seeking_talent == 'y':
            seeking_talent = True
        else:
            seeking_talent = False

        new_artist = Artist(
            name=name,
            city=city,
            state=state,
            phone=phone,
            genres=genre_objects,
            facebook_link=facebook_link,
            website=website_link,
            image_link=image_link,
            seeking_venue=seeking_talent,
            seeking_description=seeking_description

        )

        db.session.add(new_artist)
        db.session.commit()
        success = True
    except Exception as e:
        print(e)
        db.session.rollback()
        success = False
    finally:
        db.session.close()

        if success:
            flash('Artist ' + name + ' was successfully listed!')
            return render_template('pages/home.html')
        else:
            flash('An error occurred. Artist ' +
                  name + ' could not be listed.')
            return render_template('pages/home.html')

    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    # on unsuccessful db insert, flash an error instead.
    return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Shows
#  ----------------------------------------------------------------


@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # replace with real venues data.

    # Query for all of the Shows in the db
    shows = Show.query.all()

    # Create a variable to hold the Show data

    data = []

    for show in shows:
        data.append(
            {
                "venue_id": show.venue.id,
                "venue_name": show.venue.name,
                "artist_id": show.artist.id,
                "artist_name": show.artist.name,
                "artist_image_link": show.artist.image_link,
                "start_time": str(show.start_time)
            }
        )

    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db
    # upon submitting new show listing form
    # insert form data as a new Show record in the db, instead

    try:
        # artist_id
        artist_id = request.form.get("artist_id")
        # venue_id
        venue_id = request.form.get("venue_id")
        # start time
        start_time = request.form.get("start_time")

        db.session.add(
            Show(
                venue_id=venue_id,
                artist_id=artist_id,
                start_time=start_time
            )
        )
        db.session.commit()
        success = True
    except Exception as e:
        print(e)
        db.session.rollback()
        success = False
    finally:
        db.session.close()

        if success:
            flash('Show was successfully listed!')
        else:
            flash('An error occurred. Show could not be listed.')

    # on successful db insert, flash success
    # on unsuccessful db insert, flash an error instead.
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
