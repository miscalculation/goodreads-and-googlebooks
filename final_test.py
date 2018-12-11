from final import *
import unittest

class Test_Database(unittest.TestCase):
	
	def test_book(self):
		conn = sqlite.connect("asghar_maheen.sqlite")
		cur = conn.cursor()

		statement = "SELECT City from Books where title = 'The Water Nymph'"
		rows = cur.execute(statement)
		for row in rows:
			city = row[0]
		self.assertEqual(city, 'Los Angeles, California')

		statement = "SELECT Rating from Books where author = 'Christopher Pike'"
		rows = cur.execute(statement)
		for row in rows:
			city = row[0]
		self.assertEqual(city, 3.87)

		statement = '''
		Select count(1) from Books
		group by city
		having count(1) > 2
		and genre = "western"
		'''
		rows = cur.execute(statement)
		for row in rows:
			a = row[0]
		self.assertEqual(a, 3)

		statement = "SELECT City from Books where author = 'Meg Cabot'"
		rows = cur.execute(statement)
		for row in rows:
			city = row[0]
		self.assertEqual(city, 'Bloomington, Indiana')

	def test_city(self):
		conn = sqlite.connect("asghar_maheen.sqlite")
		cur = conn.cursor()

		statement = "select count(1) from cities"
		rows = cur.execute(statement)
		for row in rows:
			city = row[0]
		self.assertEqual(city, 55)

		statement = "select city from cities limit 1"
		rows = cur.execute(statement)
		for row in rows:
			city = row[0]
		self.assertEqual(city, 'Kingston-Upon-Thames')

		statement = '''select latitude from cities where city = 'London'
		'''
		rows = cur.execute(statement)
		for row in rows:
			city = row[0]
		self.assertEqual(city, 51.5073509)

class Test_Visuals(unittest.TestCase):

	def test_book_information(self):
		try:
			 book_information(2)
		except:
			self.fail()
	
	def test_author_information(self):
		try:
			 author_information(2)
		except:
			self.fail()
	
	def test_average_rating(self):
		try:
			 average_rating(2)
		except:
			self.fail()

	def test_geo_graph(self):
		try:
			 graph_books()
		except:
			self.fail() 

class Test_Helper(unittest.TestCase):
   
	def test_menu(self):
		query = helper_statement("SELECT * FROM Books ", 11)
		self.assertEqual(query, "SELECT * FROM Books  WHERE GENRE = 'mystery' ")

		query = helper_statement("", 2)
		self.assertEqual(query, " WHERE GENRE = 'autobiography' ")


if __name__ == '__main__':
	unittest.main()
