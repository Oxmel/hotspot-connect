## Avant-propos

Ce script est un prototype destiné à démontrer qu'il est techniquement
possible de transformer un hotspot 'orange' en accès internet sédentaire avec
l'aide d'un raspberry pi. Le but étant d'avoir un système de type
'set-and-forget' avec un boîtier qui prend en charge tout le processus
d'association/authentification et maintien de la connexion.

En dehors du fait que cela puisse constituer un accès internet low cost
(et illimité), les usages potentiels peuvent être assez variés.
Tel que l'établissement d'une connexion 'bas débit' à des fins de monitoring
ou pour de l'iot par exemple.

A noter qu'il est préférable (mais pas obligatoire) d'avoir plusieurs hotspots
'orange' à proximité. Car si pour une raison quelconque le hotspot courant
disparaît ou ne fontionne plus, le script cherchera automatiquement un autre
candidat dans les environs.

Ce qui (en théorie) permet d'obtenir le même avantage que celui procuré par
un réseau mesh. Avec une stabilité de connexion qui sera proportionnelle au
nombre de hotspots à portée.

## Prérequis

- Un raspberry pi sous Raspbian et ses accessoires (chargeur, carte SD,...)
- Un dongle wifi, ou le wifi intégré au raspberry (Pi 3 et Pi zero v1.3)
- Un câble ethernet
- Des identifiants orange pour pouvoir se connecter au hotspot


## Installation

Installer les dépendances et cloner le repo :

`$sudo apt-get install python-requests git`    
`$git clone https://github.com/Oxmel/hotspot-connect.git`

Editer le module `auth.py` dans le dossier `hotspot-connect/src` et
renseigner son identifiant orange (adresse mail ou numéro de mobile)
ainsi que son mot de passe.

**Attention!** Les identifiants sont pour l'instant stockés en clair,
donc à utiliser à vos risques et périls.


## Configuration du Pi

Télécharger et exécuter le script de configuration `pi-modem-router.sh` :

`$wget https://raw.githubusercontent.com/Oxmel/scripts/master/pi-modem-router.sh`    
`$sudo bash pi-modem-router.sh`

Ce script va installer et configurer dnsmasq pour offrir un serveur DHCP
sur la patte ethernet. Il va également paramétrer les interfaces réseau et
ajouter des règles iptables pour permettre au trafic de transiter entre wlan0
et eth0 (ip forwarding).

Editer le fichier `/etc/wpa_supplicant/wpa_supplicant.conf`
et ajouter ces lignes pour permettre au Pi de se connecter automatiquement
au premier point d'accès 'orange' à portée :

    country=FR
    network={
        ssid="orange"
        key_mgmt=NONE
    }

Cette méthode permet de déléguer une grosse partie du travail à wpa_supplicant
qui s'occupera lui-même d'établir et de maintenir le lien avec le hotspot.

Redémarrer le Pi.

Après redémarrage, dnsmasq devrait fournir une adresse du type `10.0.0.0/24`
au client connecté en ethernet.


## Automatisation

Une fois les étapes précédentes terminées, tester une première fois le script
'à la main' pour vérifier s'il n'y a pas d'erreurs :

`sudo python hotspot-connect.py`

Et si tout va bien, on peut ajouter un cronjob pour lancer
le script à chaque démarrage :

`$sudo crontab -e`    
`@reboot python /chemin-vers-le-script/hotspot-connect.py`

## Debugging

Ce prototype est fonctionnel en l'état mais nécessite encore beaucoup de travail
pour être considéré comme stable et sûr à utiliser. Notamment une rotation
des logs, une meilleure gestion des erreurs, une méthode plus safe pour
stocker les identifiants,...

Si quelque chose tourne mal, il est possible de consulter le fichier
de log `connect.log` à la racine du dossier `hotspot-connect` pour vérifier
d'où vient le problème. Le niveau de verbosité est réglé par défaut sur 'INFO'.
