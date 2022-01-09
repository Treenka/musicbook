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
db.init_app(app)

# connect to a local postgresql database
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

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

    results = Venue.query.filter(Venue.name.ilike('%' + text + '%')).all()
    new_response = {'count': len(results), 'data': []}

    for venue in results:
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

        past_shows = Show.query.join(Venue).filter(
            Venue.id == current_venue.id,
            Show.start_time < datetime.today()).all()

        if len(past_shows) > 0:
            for show in past_shows:
                show_dict = {
                    'artist_id': show.artist.id,
                    'artist_name': show.artist.name,
                    'artist_image_link': show.artist.image_link,
                    'start_time': str(show.start_time)
                }

                new_data['past_shows'].append(show_dict)

        upcoming_shows = Show.query.join(Venue).filter(
            Venue.id == current_venue.id,
            Show.start_time > datetime.today()).all()

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
        form = VenueForm(request.form)
        name = form.name.data

        genre_objects = []
        all_genre_names = [
            genre.name for genre in Genre.query.all()
        ]
        for genre in form.genres.data:
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
                        flash('An error occurred with genres. Venue ' +
                              name + ' could not be listed.')
                        return render_template('pages/home.html')
        if form.seeking_talent.data == 'y':
            seeking_talent = True
        else:
            seeking_talent = False

        print(f'genres: {form.genres.data}')
        print(f'genres: {type(form.genres.data)}')

        new_venue = Venue(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            address=form.address.data,
            phone=form.phone.data,
            genres=genre_objects,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website=form.website_link.data,
            seeking_talent=seeking_talent,
            seeking_description=form.seeking_description.data
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

#  ----------------------------------------------------------------
#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # displays artist data returned from the db
    artist_data = []

    for artist in Artist.query.all():
        artist_data.append({
            'id': artist.id,
            'name': artist.name})

    return render_template('pages/artists.html', artists=artist_data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # search for artists with partial
    # string search.  It is case-insensitive.

    # variable to hold the search term
    text = request.form.get('search_term', '')

    # variable to hold the amount of artists found
    results = Artist.query.filter(Artist.name.ilike('%' + text + '%')).all()

    response = {
        'count': len(results),
        'data': []
    }

    for artist in results:
        response['data'].append({
            'id': artist.id,
            'name': artist.name
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

    past_shows = Show.query.join(Artist).filter(
        Artist.id == artist.id,
        Show.start_time < datetime.today()
    ).all()
    # add past_shows data
    for show in past_shows:
        data['past_shows'].append(
            {
                'venue_id': show.venue.id,
                'venue_name': show.venue.name,
                'venue_image_link': show.venue.image_link,
                'start_time': str(show.start_time)
            }
        )
    # add upcoming_shows data
    upcoming_shows = Show.query.join(Artist).filter(
        Artist.id == artist.id,
        Show.start_time > datetime.today()
    ).all()
    for show in upcoming_shows:
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

    try:
        artist_to_edit = Artist.query.get(artist_id)
        # populate form with fields from artist with ID < artist_id >
        return render_template(
            'forms/edit_artist.html',
            form=form,
            artist=artist_to_edit
        )
    except Exception as e:
        print(e)
        flash('An error occured. Could not locate Artist to edit.')
        return render_template('pages/home.html')


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes

    try:
        form = ArtistForm(request.form)
        name = form.name.data

        # Add new genres to the db
        # create a list of genre objects

        genre_objects = []

        for genre in form.genres.data:
            if genre not in [gen.name for gen in Genre.query.all()]:
                try:
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    genre_objects.append(new_genre)
                except Exception as e:
                    print(e)
                    flash('An error occured adding the new genre')
                    return render_template('pages/home.html')
            else:
                genre_objects.append(
                    Genre.query.filter(Genre.name == genre).all()[0])

        if form.seeking_venue.data == 'y':
            seeking_venue = True
        else:
            seeking_venue = False

        # Artist selected to be editted
        artist_to_edit = Artist.query.get(artist_id)

        artist_to_edit.name = form.name.data
        artist_to_edit.city = form.city.data
        artist_to_edit.state = form.state.data
        artist_to_edit.phone = form.phone.data
        artist_to_edit.genres = genre_objects
        artist_to_edit.facebook_link = form.facebook_link.data
        artist_to_edit.image_link = form.image_link.data
        artist_to_edit.website = form.website_link.data
        artist_to_edit.seeking_venue = seeking_venue
        artist_to_edit.seeking_description = form.seeking_description.data

        db.session.commit()
        success = True
    except Exception as e:
        db.session.rollback()
        print(e)
        success = False
        error_message = e
    finally:
        db.session.close()
        if success:
            return redirect(
                url_for(
                    'show_artist',
                    artist_id=artist_id
                )
            )
        else:
            flash(f'Error: {error_message} occurred. {name} was not editted.')
            return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()

    try:
        venue = Venue.query.get(venue_id)

        # populates form with values from
        # venue with ID <venue_id>
        return render_template(
            'forms/edit_venue.html',
            form=form,
            venue=venue
        )
    except Exception as e:
        print(e)
        flash(f'An error occurred: {e}.')
        return render_template('pages/home.html')


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form
    # submitted, and update existing
    # venue record with ID <venue_id>
    # using the new attributes

    try:
        venue = Venue.query.get(venue_id)
        form = VenueForm(request.form)
        # check if the genres are in the db
        # add the genre objects to a list

        genre_objects = []

        for genre in form.genres.data:
            if genre not in [gen.name for gen in Genre.query.all()]:
                try:
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    genre_objects.append(new_genre)
                except Exception as e:
                    print(e)
                    flash('An error occured adding a genre: {e}')
            else:
                genre_objects.append(Genre.query.filter(
                    Genre.name == genre).all()[0])

        if form.seeking_talent.data == 'y':
            seeking_talent = True
        else:
            seeking_talent = False

        venue.name = form.name.data
        venue.city = form.city.data
        venue.state = form.state.data
        venue.phone = form.phone.data
        venue.genres = genre_objects
        venue.facebook_link = form.facebook_link.data
        venue.image_link = form.image_link.data
        venue.website = form.website_link.data
        venue.seeking_talent = seeking_talent
        venue.seeking_description = form.seeking_description.data

        db.session.commit()
        success = True
    except Exception as e:
        db.session.rollback()
        print(e)
        success = False
        error_message = e
    finally:
        db.session.close()
        if success:
            return redirect(url_for('show_venue', venue_id=venue_id))
        else:
            flash(f'An error occurred: {error_message}')
            return render_template('pages/home.html')

#  ----------------------------------------------------------------
#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # calls upon submitting the new artist listing form
    # insert form data as a new
    # Venue record in the db, instead
    # modify data to be the data
    # object returned from db insertion

    try:
        form = ArtistForm(request.form)
        name = form.name.data

        # create a list to hold the genres as objects
        # add new genres to the db
        genre_objects = []

        for genre in form.genres.data:
            if genre not in [gen.name for gen in Genre.query.all()]:
                try:
                    new_genre = Genre(name=genre)
                    db.session.add(new_genre)
                    genre_objects.append(new_genre)
                except Exception as e:
                    print(e)
                    flash(f'An error occurred while entering a new Genre: {e}')
                    return render_template('pages/home.html')
            else:
                genre_objects.append(Genre.query.filter(
                    Genre.name == genre).all()[0])

        if form.seeking_venue == 'y':
            seeking_venue = True
        else:
            seeking_venue = False

        new_artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            genres=genre_objects,
            facebook_link=form.facebook_link.data,
            image_link=form.image_link.data,
            website=form.website_link.data,
            seeking_venue=seeking_venue,
            seeking_description=form.seeking_description.data

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
        form = ShowForm(request.form)

        db.session.add(
            Show(
                venue_id=form.venue_id.data,
                artist_id=form.artist_id.data,
                start_time=form.start_time.data
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
