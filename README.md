# 507 Final Project
# Exploring Books and Authors of Different Genres

## Overview

This program that lets the user browse through various book genres (ie Mystery, Action, Romance) and displays various analyses of the books.  

## Data Sources
Google Books API: Takes in multiple genres (twenty-six) and returns information about individual book's titles, authors, ISBNs (must look for the thirteen digit ISBN and not the ten digit one), publishers, publish dates, descriptions, and ratings. 
Goodreads API: ISBN is used to find information on the book and the author, including the author's Goodreads ID. (Requires authenthication). 
Goodreads API: Goodreads Author ID is used to query information on the author, including their hometown. (Requires authenthication). 
Google Geocoding API: After obtaining the hometown city, the Google Geocoding API was utilized to get the latitude and longitude of the hometown. (Requires authenthication). 

## Visualizations 

<img src="https://github.com/miscalculation/Final_Project/blob/master/example_visualizations/table-of-book-data.png" alt="alt text" width="300">
<img src="https://github.com/miscalculation/Final_Project/blob/master/example_visualizations/table-of-author-data.png" alt="alt text" width="300">
<img src="https://github.com/miscalculation/Final_Project/blob/master/example_visualizations/pandas-bar-chart.png" alt="alt text" width="300">
<img src="https://github.com/miscalculation/Final_Project/blob/master/example_visualizations/plot%20from%20API.png" alt="alt text" width="300">
