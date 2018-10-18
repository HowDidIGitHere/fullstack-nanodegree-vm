# Item Catalog App

This application allows users to go through a catalog of sporting equipment sectioned into their respective categories. All users are able to sign in through the third party, Google. This verification system allows users to add, edit, and delete items from their own catalog. Withholding from the default set of items already added for all users.

## Instructions

The Item Catalog App requires three resources not included in the zipped item-catalog-project folder. To run this program; Python, VirtualBox, and Vagrant must be downloaded. You can find these from the following links:

Download Python version 3 at
https://www.python.org/downloads/

VirtualBox at
https://www.virtualbox.org/wiki/Downloads

Vagrant at
https://www.vagrantup.com/downloads.html

All other required files; application.py, client_secrets.json, itemcatalogwithusers.db, styles.css and templates, can be downloaded from the zipped item-catalog-project folder. Once all resources have been successfully downloaded, you must initiate the virtual machine via linux.

```
$ vagrant up
$ vagrant ssh
```

With your newly installed virtual machine up and running you need to change directories to /vagrant and then you are all set to initiate the application with these commands:

```
$ cd /vagrant
$ python application.py
```

This will provide you with the entire item catalog application.
