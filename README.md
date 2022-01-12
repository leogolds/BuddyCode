# HOWTO
1. Clone repo
2. cd into repo
3. docker-compose up -d
4. App will be available on port 80
5. REST API available on port 9000 (openapi documentation available on ':9000/docs')
6. DB management available on port 8081

# Features
* Modern editor widget based on [Ace](https://ace.c9.io/)
* Real time, multi user code editor
* Long term document storage in a DB
* Differential synchronization provides best effort merging while avoiding merge collisions (as per [Differential Synchronization - Neil Fraser](https://neil.fraser.name/writing/sync/))

# Architecture
## Frontend
Single page website with embedded JavaScript. Frontend provides an editor widget (Ace) and periodically syncs document state through a REST API. Patches served by the REST API are applied on a best effort basis while maintaining user cursor/selection state.
## Cache
Cache implemented as a REST API ([FastAPI](https://fastapi.tiangolo.com/)) with two endpoints:
1. Get Latest Data - provides current document state based on cached/db version
2. Post Update - provides a facility for frontend to post document patches. Each client update gets a response from the cache with a patch for updating clientside document to current state.

The cache maintains the current state of active documents and periodically dumps them to the backend DB. Stale documents get cleaned up during the DB sync procedure.
## Backend
1. mongodb server based on vanilla image
2. mongo-express management ui based on vanilla image



# TODO
- [ ] Key/secret distribution
- [x] Periodic cache cleanup - clean up cached document with access time > 10 minutes 
- [x] Smarter db synchronization - cache dumps active documents to db every 2 minutes
- [ ] Chat?
- [x] Make url parameters appear on first load as oppsed to when document id changes
- [ ] Track user stats (connections/disconnections/editor access)
- [x] Maintain cursor position/selection on document update