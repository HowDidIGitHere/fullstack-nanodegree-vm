from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    jsonify
)
from flask import session as login_session
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from itertools import chain
import random
import string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2
import json
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(open('client_secrets.json',
                            'r').read())['web']['client_id']
APPLICATION_NAME = 'Item Catalog Application'

engine = create_engine('sqlite:///itemcatalogwithusers.db'
                       '?check_same_thread=False')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# JSON Endpoints
@app.route('/catalog/JSON')
def mainMenuJSON():
    items = session.query(Item).all()
    return jsonify(items=[item.serialize for item in items])


@app.route('/catalog/<category_name>/items/JSON')
def catalogMenuJSON(category_name):
    items = session.query(Item).filter_by(category_name=category_name).all()
    return jsonify(items=[item.serialize for item in items])


@app.route('/catalog/<category_name>/<item_name>/JSON')
def catalogItemJSON(category_name, item_name):
    item = session.query(Item).filter_by(name=item_name).one()
    return jsonify(item=item.serialize)


# Shows the categories in one column and latest items in another
# Being logged in gives option to add item
@app.route('/')
@app.route('/catalog/')
def mainMenu():
    category = session.query(Category).all()
    categories = session.query(Category).order_by(asc(Category.name))
    publicItems = session.query(Item)\
        .filter_by(user_id=1).order_by(asc(Item.id))
    if 'username' not in login_session:
        return render_template('publicMainMenu.html',
                               category=category,
                               categories=categories,
                               items=publicItems)
    else:
        privateItems = session.query(Item)\
            .filter_by(user_id=login_session['user_id']).order_by(asc(Item.id))
        items = list(chain(publicItems, privateItems))
        return render_template('mainMenu.html',
                               category=category,
                               categories=categories,
                               items=items)


# Shows the categories and the items of a chosen category in two columns
# Being logged in gives option to add item
@app.route('/catalog/<category_name>/')
@app.route('/catalog/<category_name>/items/')
def catalogMenu(category_name):
    categories = session.query(Category).order_by(asc(Category.name))
    chosenCata = session.query(Category).filter_by(name=category_name).one()
    publicItems = session.query(Item)\
        .filter_by(category_name=category_name, user_id=1).all()
    publicNumItem = session.query(Item)\
        .filter_by(category_name=category_name, user_id=1).count()
    if 'username' not in login_session:
        return render_template('publicCatalogMenu.html',
                               numItem=publicNumItem,
                               categories=categories,
                               chosenCata=chosenCata,
                               items=publicItems)
    else:
        privateItems = session.query(Item)\
            .filter_by(category_name=category_name,
                       user_id=login_session['user_id']).all()
        items = list(chain(publicItems, privateItems))
        privateNumItem = session.query(Item)\
            .filter_by(category_name=category_name,
                       user_id=login_session['user_id']).count()
        numItem = publicNumItem + privateNumItem
        return render_template('catalogMenu.html',
                               numItem=numItem,
                               categories=categories,
                               chosenCata=chosenCata,
                               items=items)


# Shows the description of an item
# Being logged in gives option to Edit/Delete
@app.route('/catalog/<category_name>/<item_name>/')
def catalogItem(category_name, item_name):
    item = session.query(Item).filter_by(name=item_name).one()
    creator = getUserInfo(item.user_id)
    if 'username' not in login_session:
        return render_template('publicCatalogItem.html', item=item)
    elif creator.id != login_session['user_id']:
        return render_template('notCreatorCatalogItem.html', item=item)
    else:
        return render_template('catalogItem.html', item=item)


# Adds new item to catalog
# Only viewable if logged in
@app.route('/catalog/add/', methods=['GET', 'POST'])
def addItem():
    categories = session.query(Category).order_by(asc(Category.name))
    if 'username' not in login_session:
        return redirect('/')
    else:
        if request.method == 'POST':
            newItem = Item(name=request.form['name'],
                           description=request.form['description'],
                           category_name=request.form['category_name'],
                           user_id=login_session['user_id'])
            session.add(newItem)
            session.commit()
            return redirect(url_for('mainMenu'))
        return render_template('addItem.html', categories=categories)


# Shows the options to edit a specific item
# Only viewable if logged in
@app.route('/catalog/<item_name>/edit/', methods=['GET', 'POST'])
def editItem(item_name):
    editedItem = session.query(Item).filter_by(name=item_name).one()
    categories = session.query(Category).order_by(asc(Category.name))
    creator = getUserInfo(editedItem.user_id)
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return redirect('/')
    else:
        if request.method == 'POST':
            if request.form['name']:
                editedItem.name = request.form['name']
            if request.form['description']:
                editedItem.description = request.form['description']
            if request.form['category_name']:
                editedItem.category_name = request.form['category_name']
            session.add(editedItem)
            session.commit()
            return redirect(url_for('mainMenu'))
        return render_template('editItem.html',
                               categories=categories,
                               item=editedItem)


# Asks whether you wish to delete a specific item
# Only viewable if logged in
@app.route('/catalog/<item_name>/delete/', methods=['GET', 'POST'])
def deleteItem(item_name):
    itemToDelete = session.query(Item).filter_by(name=item_name).one()
    creator = getUserInfo(itemToDelete.user_id)
    if 'username' not in login_session or \
            creator.id != login_session['user_id']:
        return redirect('/')
    else:
        if request.method == 'POST':
            session.delete(itemToDelete)
            session.commit()
            return redirect(url_for('mainMenu'))
        return render_template('deleteItem.html', item=itemToDelete)


# Allows users to login
@app.route('/login')
def login():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)


# Google connect path
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])

    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    login_session['provider'] = 'google'

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; ' \
              'height: 300px;' \
              'border-radius: 150px;' \
              '-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    return output


# Google disconnect path
@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(
            json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response


# General disconnect path for future implementation of more login providers
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash('You have successfully been logged out.')
        return redirect(url_for('mainMenu'))
    else:
        flash('You were not logged in')
        return redirect(url_for('mainMenu'))


# Group of functions that allow for login user generation
def createUser(login_session):
    newUser = User(name=login_session['username'],
                   email=login_session['email'],
                   picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
