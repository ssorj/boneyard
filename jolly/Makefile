jolly.db: jolly.xml
	./jolly.py jolly.xml jolly.

flimsy.html: flimsy.sql jolly.db
	sqlite3 -html -header jolly.db < $< > $@.tmp
	echo "<table>" > $@
	cat $@.tmp >> $@
	echo "</table>" >> $@
	rm $@.tmp

plucky.txt: plucky.sql jolly.db
	sqlite3 -column jolly.db < $< > $@
