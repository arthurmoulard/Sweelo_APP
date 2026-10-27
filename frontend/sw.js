/**
 * Sweelo — Service worker (PWA)
 *
 * Un service worker est un script que le navigateur exécute en arrière-plan,
 * entre l'application et le réseau. Ici, il a deux rôles :
 *   1. rendre Sweelo installable sur l'écran d'accueil d'un téléphone ;
 *   2. garder en cache les fichiers qui ne changent presque jamais (styles,
 *      logo, icônes) pour qu'ils s'affichent même sans connexion.
 *
 * Stratégie « réseau d'abord » : on demande toujours la version à jour au
 * serveur, et on ne se sert du cache que si le réseau ne répond pas.
 * Les appels à l'API (/api/...) ne sont jamais mis en cache : les données
 * (feed, activités, profil) viennent toujours du serveur.
 */

const CACHE_NAME = 'sweelo-v1';

const FICHIERS_STATIQUES = [
  '/nav.css',
  '/shared/auth.js',
  '/shared/admin-nav.js',
  '/files/sweelo-logo.png',
  '/files/icon-feed.png',
  '/files/icon-profile.png',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
];

// Installation : on met les fichiers statiques en cache
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(FICHIERS_STATIQUES))
  );
  self.skipWaiting();
});

// Activation : on supprime les anciens caches (ex. sweelo-v0) après une mise à jour
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((noms) =>
      Promise.all(noms.filter((nom) => nom !== CACHE_NAME).map((nom) => caches.delete(nom)))
    )
  );
  self.clients.claim();
});

// Chaque requête de l'application passe par ici
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // On ne touche ni aux envois de données, ni aux autres sites, ni à l'API
  if (event.request.method !== 'GET' || url.origin !== self.location.origin
      || url.pathname.startsWith('/api/')) {
    return;
  }

  // Réseau d'abord ; si pas de connexion, version en cache
  event.respondWith(
    fetch(event.request).catch(() => caches.match(event.request))
  );
});
