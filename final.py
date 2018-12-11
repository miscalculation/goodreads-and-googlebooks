from __future__ import with_statement
from requests_oauthlib import OAuth1
import json
import sys
import requests
from bs4 import BeautifulSoup
import sqlite3 as sqlite
import xmltodict 
import re
import pandas as pd
import plotly.plotly as py
import plotly.graph_objs as go
from plotly import tools
from clint.textui import puts, indent, colored
import secret

key = secret.GOODREADS_KEY
googlekey = secret.GOOGLEMAP_KEY

# # SI 507 - Final Project
# # COMMENT WITH: Maheen Asghar
# # Your section day/time: 002

def initialize_db():
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()
	
	statement = '''
		DROP TABLE IF EXISTS 'Cities';
	'''
	cur.execute(statement)

	statement = '''
		DROP TABLE IF EXISTS 'Books';
	'''
	cur.execute(statement)
	
	conn.commit()
	
	statement = '''
		CREATE TABLE 'Cities' (
			'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'City' TEXT NOT NULL,
			'Latitude' REAL,
			'Longitude' REAL
		);
	'''
	cur.execute(statement)
	
	statement = '''
		CREATE TABLE 'Books' (
			'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
			'Genre' TEXT NOT NULL,
			'Title' TEXT NOT NULL,
			'Author' TEXT NOT NULL,
			'ISBN' INTEGER NOT NULL,
			'Publisher' TEXT,
			'PublishedDate' TEXT,
			'Description' TEXT,
			'Rating' REAL,
			'AuthorId' INTEGER,
			'City' TEXT,
			'CityId' INTEGER,
			FOREIGN KEY('CityId') REFERENCES Cities ('Id')   
		);
	'''
	cur.execute(statement)

	conn.close() 

	return None

#This function hits the google api to get the genres of books if they don't already exist in the cache. It then inserts all the data into the database table called 'Books.'
def get_google_data(genres):
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	CACHE_FNAME = "googlebookscache.json" 
	try:
		with open(CACHE_FNAME, "rb") as f:
			CACHE_DICTION = json.load(f)
		f.closed
	except:
		CACHE_DICTION = {}
	
	baseurl = "https://www.googleapis.com/books/v1/volumes?q=subject:"	
	
	if genres[0] in CACHE_DICTION:
		print("Getting cached google data...")	
		
	else:
		print("Fetching new google data...") 
		for genre in genres:
			resp = requests.get(baseurl + genre)
			CACHE_DICTION[genre] = json.loads(resp.text)

		f = open(CACHE_FNAME,"w")
		cache_str_tmp = json.dumps(CACHE_DICTION)
		f.write(cache_str_tmp)
		f.close()  

	for genre in CACHE_DICTION:
		#print(CACHE_DICTION[genre])
		for book in CACHE_DICTION[genre]["items"]:
			try:
				title = book["volumeInfo"]["title"]
				author = book["volumeInfo"]["authors"][0]
				for c in book["volumeInfo"]["industryIdentifiers"]:
					if c["type"] == "ISBN_13":
						new_isbn = c["identifier"]
				publisher = book["volumeInfo"]["publisher"]
				publishdate = book["volumeInfo"]["publishedDate"]
				description = book["volumeInfo"]["description"]
				insertion = (genre, title, author, new_isbn, publisher, publishdate, description)
				#print(insertion)
				statement = 'INSERT INTO "Books" (Genre, Title, Author, ISBN, Publisher, PublishedDate, Description)'
				statement += 'VALUES (?, ?, ?, ?, ?, ?, ?)'
				cur.execute(statement, insertion)
				conn.commit()
			except:
				pass	
				
		
	conn.close()
	return None

#This function hits the goodreads api to get the author id of the author of the book if they don't already exist in the cache. It then inserts all the data into the database table called 'Books.'
def get_goodreads_author_data():
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	CACHE_FNAME = "goodreadsauthorcache.json" 
	try:
		with open(CACHE_FNAME, "rb") as f:
			CACHE_DICTION = json.load(f)
		f.closed
	except:
		CACHE_DICTION = {}

	statement = 'SELECT ISBN FROM Books'
	rows = cur.execute(statement)
	
	isbns = []
	for row in rows:
		isbns.append(str(row[0]))
	
	if isbns[0] in CACHE_DICTION:
		print("Getting cached author data...")	
		
	else:
		print("Fetching new author data...") 
		
		for isbn in isbns:
			baseurl = "https://www.goodreads.com/search/index.xml?key=" + key + "&q=" + str(isbn) 
			resp = requests.get(baseurl)
			o = xmltodict.parse(resp.text)
			json_string = json.dumps(o)
			json_actual = json.loads(json_string)
			CACHE_DICTION[isbn] = json_actual
		
		f = open(CACHE_FNAME,"w")
		cache_str_tmp = json.dumps(CACHE_DICTION)
		f.write(cache_str_tmp)
		f.close()  
		
	
	for a in CACHE_DICTION:
		try:
			#print(a)
			author = CACHE_DICTION[a]["GoodreadsResponse"]['search']['results']['work']["best_book"]['author']['id']['#text']
			rating = CACHE_DICTION[a]["GoodreadsResponse"]['search']['results']['work']["average_rating"]
			if rating == {'@type': 'float', '#text': '0.0'}:
				rating = 0.00
			print(author)
			print(rating)
			statement = '''UPDATE "Books"
			SET AUTHORID = ?,
			RATING = ?
			WHERE ISBN = ? 
			'''
			cur.execute(statement,(author,rating,a,))
			conn.commit()
			
		except: 
			pass
	
	conn.close()
	return None


#This function hits the goodreads api again using the author id to get their hometown city if they don't already exist in the cache. It then inserts all the data into the database table called 'Books.'
def get_goodreads_city_data():

	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	CACHE_FNAME = "goodreadscitycache.json" 
	try:
		with open(CACHE_FNAME, "rb") as f:
			CACHE_DICTION = json.load(f)
		f.closed
	except:
		CACHE_DICTION = {}

	statement = 'SELECT AuthorId FROM Books'
	rows = cur.execute(statement)
	authorids = []
	for row in rows:
		authorids.append(str(row[0]))
	
	if authorids[0] in CACHE_DICTION:
		print("Getting cached city data...")	
		
	else:
		print("Fetching new city data...") 

		for authorid in authorids:
			baseurl = "https://www.goodreads.com/author/show.xml?key=" + key + "&id=" + str(authorid) 
			resp = requests.get(baseurl)
			o = xmltodict.parse(resp.text)
			json_string = json.dumps(o)
			json_actual = json.loads(json_string)
			CACHE_DICTION[authorid] = json_actual
		
		f = open(CACHE_FNAME,"w")
		cache_str_tmp = json.dumps(CACHE_DICTION)
		f.write(cache_str_tmp)
		f.close()  

	
	for a in CACHE_DICTION:
		try:
			city = CACHE_DICTION[a]['GoodreadsResponse']['author']['hometown']
			statement = '''UPDATE "Books"
			SET CITY = ?
			WHERE AUTHORID = ? 
			'''
			cur.execute(statement,(city,a,))
			conn.commit()		
		except:
			pass

	statement = '''SELECT DISTINCT CITY FROM "Books" where city is not null'''
	rows = cur.execute(statement)
	city_list = []
	for row in rows:		
		city_list.append(str(row[0]))
	
	for city in city_list:
		cur.execute('INSERT into "Cities" (City) values (?)', (city,))
		conn.commit()
		
	
	statement = '''UPDATE "Books"
			SET CityId = (SELECT ID FROM "Cities" WHERE CITY = Books.City)
			'''
	cur.execute(statement)
	conn.commit()

	conn.close()
	return None

#This function hits the goolge geo api to get latitude and longitude of the authors hometowns if they don't already exist in the cache. It then inserts all the data into the database table called 'Cities.'
def get_geo_data():
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	CACHE_FNAME = "geocache.json" 
	try:
		with open(CACHE_FNAME, "rb") as f:
			CACHE_DICTION = json.load(f)
		f.closed
	except:
		CACHE_DICTION = {}

	statement = 'SELECT City FROM Cities'
	rows = cur.execute(statement)
	cities = []
	for row in rows:
		cities.append(str(row[0]))
	
	if cities[0] in CACHE_DICTION:
		print("Getting cached city data...")	
		
	else:
		print("Fetching new city data...") 

		for city in cities:
			newName = re.sub('[\\\\/:*?"<>{},.()|]', '', city)
			newCity = re.sub('-', ' ', newName)
			fixedCity = re.sub(' ', '+', newName)
			print(fixedCity)
			
			baseurl = "https://maps.googleapis.com/maps/api/geocode/json?address=" + fixedCity + "&key=" + googlekey
			resp = requests.get(baseurl)
			CACHE_DICTION[city] = json.loads(resp.text)
		
		f = open(CACHE_FNAME,"w")
		cache_str_tmp = json.dumps(CACHE_DICTION)
		f.write(cache_str_tmp)
		f.close()  

	
	for a in CACHE_DICTION:
		try:
			lat = CACHE_DICTION[a]['results'][0]['geometry']['location']["lat"]
			lng = CACHE_DICTION[a]['results'][0]['geometry']['location']["lng"]
			statement = '''UPDATE "Cities"
			SET Latitude = ?,
			Longitude = ?			
			WHERE City = ? 
			'''
			cur.execute(statement,(lat, lng, a,))
			conn.commit()	
		except:
			pass

	conn.close()
	return None

def helper_menu():
	puts(colored.magenta("****************************************"))
	with indent(4):
		puts("1. art")
		puts("2. autobiography")
		puts("3. biography")
		puts("4. children")
		puts("5. comic")
		puts("6. drama")
		puts("7. health")
		puts("8. history")
		puts("9. horror")
		puts("10. memoir")
		puts("11. mystery")
		puts("12. poetry")
		puts("13. religion")
		puts("14. romance")
		puts("15. thriller")
		puts("16. tragedy")
		puts("17. travel")
		puts("18. western")
	puts(colored.magenta("****************************************"))

	while True:
		try:
			reply =  int(input("\nPlease pick a genre: \n"))
		except ValueError:
			puts(colored.red("Please enter a valid number between 1 and 18."))
			continue

		if reply < 0:
			puts(colored.red("Please enter a number between 1 and 18."))
			continue
		elif reply > 18:
			puts(colored.red("Please enter a number between 1 and 18."))
			continue
		else:
			break

	return reply

def helper_statement(statement, reply):
	if reply == 1:
		statement += " WHERE GENRE = 'art' "
	if reply == 2:
		statement += " WHERE GENRE = 'autobiography' "
	if reply == 3:
		statement += " WHERE GENRE = 'biography' "
	if reply == 4:
		statement += " WHERE GENRE = 'children' "
	if reply == 5:
		statement += " WHERE GENRE = 'comic' "
	if reply == 6:
		statement += " WHERE GENRE = 'drama' "
	if reply == 7:
		statement += " WHERE GENRE = 'health' "
	if reply == 8:
		statement += " WHERE GENRE = 'history' "
	if reply == 9:
		statement += " WHERE GENRE = 'horror' "
	if reply == 10:
		statement += " WHERE GENRE = 'memoir' "
	if reply == 11:
		statement += " WHERE GENRE = 'mystery' "
	if reply == 12:
		statement += " WHERE GENRE = 'poetry' "
	if reply == 13:
		statement += " WHERE GENRE = 'religion' "
	if reply == 14:
		statement += " WHERE GENRE = 'romance' "
	if reply == 15:
		statement += " WHERE GENRE = 'thriller' "
	if reply == 16:
		statement += " WHERE GENRE = 'tragedy' "
	if reply == 17:
		statement += " WHERE GENRE = 'travel' "
	if reply == 18:
		statement += " WHERE GENRE = 'western' "

	return statement 

def book_information(reply):
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	statement = '''SELECT Genre, Title, Author, ISBN, Publisher, PublishedDate,  Rating, 
	CASE WHEN City is NULL THEN 'Unknown' 
	Else City end as city  
	FROM Books '''
	
	if reply == 1:
		genre = helper_menu()
		new_statement = helper_statement(statement, genre)
	else:
		new_statement = statement
	
	df = pd.read_sql_query(new_statement, conn)
	
	table = go.Table(
		#columnwidth=[0.4, 0.47, 0.48, 0.4, 0.4, 0.45, 0.5, 0.6],
		header=dict(
			#values=list(df.columns[1:]),
			values=['Genre', 'Title', 'Author', 'ISBN', 'Publisher', 'PublishedDate', 'Rating', 'City'],
			font=dict(size=10),
			line = dict(color='rgb(50, 50, 50)'),
			align = 'left',
			fill = dict(color='#d562be'),
		),
		cells=dict(
			values=[df[k].tolist() for k in df.columns[0:]],
			line = dict(color='rgb(50, 50, 50)'),
			align = 'left',
			fill = dict(color='#f5f5fa')
		)
	)
	py.plot([table], filename='table-of-book-data')
	return None

def author_information(reply):
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	statement = '''SELECT B.Genre, B.Author,
		CASE WHEN B.City is NULL THEN 'Unknown' 
		Else B.City end as city,
		CASE WHEN C.Latitude is NULL THEN 'Unknown' 
		Else C.Latitude end as Latitude,
		CASE WHEN C.Longitude is NULL THEN 'Unknown' 
		Else C.Longitude end as Longitude
		FROM Books B
	left join Cities C
	on B.CityId = C.Id
	'''
	
	if reply == 1:
		genre = helper_menu()
		new_statement = helper_statement(statement, genre)
	else:
		new_statement = statement

	df = pd.read_sql_query(new_statement, conn)
	
	#print(df)
	table = go.Table(
		#columnwidth=[0.4, 0.47, 0.48, 0.4, 0.4, 0.45, 0.5, 0.6],
		header=dict(
			#values=list(df.columns[1:]),
			values=['Genre', 'Title', 'Author', 'ISBN', 'Publisher', 'PublishedDate', 'Rating', 'City'],
			font=dict(size=10),
			line = dict(color='rgb(50, 50, 50)'),
			align = 'left',
			fill = dict(color='#d562be'),
		),
		cells=dict(
			values=[df[k].tolist() for k in df.columns[0:]],
			line = dict(color='rgb(50, 50, 50)'),
			align = 'left',
			fill = dict(color='#f5f5fa')
		)
	)
	py.plot([table], filename='table-of-author-data')
	return None

def average_rating(reply):
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()

	statement = '''Select Genre, Round(AVG(Rating), 2) as Rating
		from Books
	'''
	
	if reply == 1:
		genre = helper_menu()
		new_statement = helper_statement(statement, genre)
	else:
		new_statement = statement

	new_statement += ' Group by Genre '
	df = pd.read_sql_query(new_statement, conn)
	
	data = [
		go.Bar(
			x=df['Genre'], # assign x as the dataframe column 'x'
			y=df['Rating']
		)
	]

	py.plot(data, filename='pandas-bar-chart')

	return None


def graph_books():
	conn = sqlite.connect("asghar_maheen.sqlite")
	cur = conn.cursor()
	
	text_list = []
	latitude_list = []
	longitude_list = []
	data = []
	
	statement = '''Select B.Genre, B.Title, B.Author, B.City , C.Latitude, C.Longitude
		from Books B, Cities C
		Where B.CityId = C.id
	'''	
	rows = cur.execute(statement)

	for row in rows:
		text_list.append(row[0] + "<br>" + row[1] + "<br>" + row[2] + "<br>" + row[3])
		latitude_list.append(row[4])
		longitude_list.append(row[5])

	data = [		
		dict(
		type = 'scattergeo',
		lon = longitude_list,
		lat = latitude_list,
		text = text_list,			
		mode = 'markers',
		marker = dict(
			color= 'rgb(0,116,217)',
			size = 8,
			sizemode = 'diameter'
		))
	]
	
	layout = go.Layout(
	title = 'Author Hometowns',
	showlegend = True,
	geo = dict(
			scope='world',
			projection=dict( type = 'natural earth'),
			showland = True,
			landcolor = 'rgb(217, 217, 217)',
			subunitwidth=1,
			countrywidth=1,
			subunitcolor="rgb(255, 255, 255)",
			countrycolor="rgb(255, 255, 255)"
		),)

	fig =  go.Figure(layout=layout, data=data)
	py.plot( fig, validate=False)

	return None

def mainmenu():
	print("\bPlease select an option below and type '0' to exit the program.")
	puts(colored.cyan("----------------------------------------"))
	print("\t\tMain Menu")
	puts(colored.cyan("----------------------------------------"))
	with indent(4):
		puts('1. Book Information')
		puts('2. Author Information')
		puts('3. Average Rating of Book')
		puts("4. Graph Author's Hometowns")
	puts(colored.cyan("----------------------------------------"))
	
	while True:
		try:
			option =  int(input("\nWhat data would you like to explore?\n"))
		except ValueError:
			puts(colored.red("Please enter a valid number between 1 and 4."))
			continue

		if option < 0:
			puts(colored.red("Please enter a number between 1 and 4."))
			continue
		elif option > 4:
			puts(colored.red("Please enter a number between 1 and 4."))
			continue
		elif option == 0:
			raise SystemExit
		else:
			break
	
	submenu(option)
	
	return None

def submenu(option):
	if option == 1 or option == 2 or option == 3:
		puts(colored.magenta("----------------------------------------"))
		with indent(4):
			puts('1. Genre')
			puts('2. All')
		puts(colored.magenta("----------------------------------------"))

		while True:
			try:
				reply =  int(input("\nWhat data would you like to explore?\n"))
			except ValueError:
				puts(colored.red("Please enter a valid number between 1 and 2."))
				continue

			if reply < 0:
				puts(colored.red("Please enter a number between 1 and 2"))
				continue
			elif reply > 2:
				puts(colored.red("Please enter a number between 1 and 2."))
				continue
			else:
				break

	if option == 1:
		book_information(reply)
		mainmenu()
	elif option == 2:
		author_information(reply)
		mainmenu()
	elif option == 3:
		average_rating(reply)
		mainmenu()
	elif option == 4:
		graph_books()
		mainmenu()
	else:
		print("Error")


if __name__ == "__main__":
	genres = ["romance", "mystery", "western", "horror", "drama", "history", "biography", "comic", "thriller", "health", "travel", "religion", "poetry", "art", "tragedy", "children", "autobiography", "memoir"]
	#initialize_db()
	#get_google_data(genres)
	#get_goodreads_author_data()
	#get_goodreads_city_data()
	#get_geo_data()
	mainmenu()
	