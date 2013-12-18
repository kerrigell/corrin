#!/bin/bash

TABLES=`mysql -e 'SHOW TABLES FROM dbpizza' | tail -n +2 | egrep -v 'django_|auth_'`
mysqldump --no-data dbpizza ${TABLES[@]} | sed 's/ AUTO_INCREMENT=[0-9]\+//g' > ./dbpizza.sql
