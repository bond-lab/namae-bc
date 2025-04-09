cd ~/git/namae-bc
rsync -avz web wsgi.py requirements.txt compling.upol.cz:/var/www/namae/



got to  compling.upol.cz

### Must use the smae version of python as used by apache
###
### sudo grep mod_wsgi /var/log/apache2/error.log
###

$ sudo  apt install python3.8-venv
$ cd /var/www/namae/
$ python3.8 -m venv .venv
$ source .venv/bin/activate
$ python -m pip install --upgrade pip
$ pip install -r requirements.txt

sudo  chown -R bond:www-data /var/www/namae/



Added to: /etc/apache2/sites-available/000-default-le-ssl.conf

###
### Namae
###

	WSGIDaemonProcess namae user=www-data group=www-data threads=5  python-home=/var/www/namae/.venv
	WSGIScriptAlias /namae /var/www/namae/namae.wsgi
	<Directory /var/www/namae/>
		WSGIProcessGroup namae
		WSGIApplicationGroup %{GLOBAL}
		WSGIScriptReloading On
		Require all granted
	</Directory>
 
$ sudo systemctl restart apache2
