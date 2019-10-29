## Hotspot Connect - v0.x

Automatise le processus de connexion sur un hotspot *orange*.

Le but ici est de transformer un hotspot *orange* en accès internet
sédentaire à l'aide d'un Raspberry Pi. Pour cela on copie le fonctionnement
classique d'un modem-routeur où la partie modem assure l'accès à internet,
et la partie routeur assure, entre autres, l'adressage et la gestion des
clients.

Dans le cas présent, la partie modem va être assurée par le script
hotspot-connect qui va prendre en charge tout le processus de connexion.
Ce qui comprend la recherche de points d'accès disponibles, l'association
avec le hotspot, l'authentification sur le portail captif, ainsi que la
surveillance et le maintien de la connexion sur la durée.

Un deuxième script va quant à lui se charger de configurer le Raspberry Pi
en mode routeur pour offrir un serveur DHCP et partager la connexion
internet. Et une fois qu'on a automatisé l'ensemble du processus
(voir plus bas), le Raspberry Pi adopte le même comportement que celui
d'une box internet quelconque.

A noter qu'il est préférable (mais pas obligatoire) d'avoir plusieurs
hotspots *orange* à proximité. Car si le hotspot courant disparaît ou ne
fonctionne plus, le script cherchera automatiquement un autre candidat dans
les environs.

## Prérequis

- Un Raspberry Pi sous Raspbian et ses accessoires (chargeur, carte SD,...)
- Un dongle wifi, ou le wifi intégré au raspberry (Pi 3, Pi 4 et Pi Zero W)
- Des identifiants orange pour pouvoir se connecter au hotspot
- Un câble ethernet

## Installation

Installer les dépendances et cloner le repo :

    $ sudo apt-get install python-requests git
    $ git clone https://github.com/Oxmel/hotspot-connect.git

Editer le module `auth.py` dans le dossier `hotspot-connect/src` et
renseigner son identifiant orange (adresse mail ou numéro de mobile)
ainsi que son mot de passe :

    username = '0601020304'
    password = 'mot_de_passe'

**Attention!** Les identifiants sont pour l'instant stockés en clair,
donc à utiliser à vos risques et périls.

## Configuration du Pi

Télécharger et exécuter le script de configuration `pi-modem-router.sh` :

    $ wget https://raw.githubusercontent.com/Oxmel/scripts/master/pi-modem-router.sh
    $ sudo bash pi-modem-router.sh

Ce script va installer un serveur DHCP (dnsmasq) et ajouter des règles iptables
pour faire transiter le trafic entre les interfaces wlan et lan (ip forwarding).

Redémarrer le Pi.

Après redémarrage, dnsmasq attribuera l'adresse `10.0.0.1` au Pi et
l'adresse `10.0.0.2` au client connecté en ethernet.

## Automatisation

Une fois les étapes précédentes terminées, tester une première fois le script
à la main pour vérifier s'il n'y a pas d'erreurs :

    ~Projets/hotspot-connect$ python hotspot-connect.py
    20/10/2019 22:16:52 - [INFO]: Hotspot Connect v0.x
    20/10/2019 22:16:52 - [INFO]: Looking for 'orange' hotspots...
    20/10/2019 22:16:56 - [INFO]: Found 3 candidate(s) in the area
    20/10/2019 22:16:56 - [INFO]: Association in progress...
    20/10/2019 22:17:01 - [INFO]: Association successfull :-)
    20/10/2019 22:17:01 - [INFO]: bssid  : 1a:2b:3c:4d:5e:6f
    20/10/2019 22:17:01 - [INFO]: signal : -65 dBm
    20/10/2019 22:17:03 - [INFO]: Authentication required on the captive portal
    20/10/2019 22:17:03 - [INFO]: Sending credentials...
    20/10/2019 22:17:08 - [INFO]: Authentication successfull
    20/10/2019 22:17:08 - [INFO]: Network monitoring enabled


Et si tout va bien, on peut ajouter un cronjob pour automatiser le processus
à chaque reboot :

    $ crontab -e
    @reboot python /chemin-vers-le-script/hotspot-connect.py

## Debugging

Ce prototype est fonctionnel en l'état mais reste encore à un stade très
expérimental, ce qui peut impliquer pas mal de petits désagréments comme
des erreurs inattendues, des pertes de connexions aléatoires, des crash
silencieux, etc...

En cas d'erreur, il est possible de consulter le fichier de log `connect.log`
à la racine du dossier `hotspot-connect` pour vérifier d'où vient le problème.
Le niveau de verbosité est réglé par défaut sur `INFO`.
