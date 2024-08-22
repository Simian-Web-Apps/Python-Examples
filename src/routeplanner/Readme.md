# EV Truck route "planner"
For local or self deployed usage: 
1. [Create a (free) https://openrouteservice.org/ account](https://openrouteservice.org/dev/#/signup) and get your API key (token).
2. [Create a (free) https://here.com/ account](https://platform.here.com/portal/) and get your API key. 
3. Copy the `local_application_data.json.sample` to `local_application_data.json`.
4. Store your openstreetroute.org API key (token) as `open_route_service_api_key` in `local_application_data.json`.
5. Store your here.com API key as `here_api_key` in `local_application_data.json`.
6. Optionally set `here_frontend_autocomplete_delay` and `here_backend_lookup_interval` values to higher values to reduce request rates to here.com.
7. Make sure that simian-gui is installed (see `requirements.txt`), and for local/development use simian-local.

To start the application locally run `route_planner.py`.

Note: This app uses truck images from `https://downloads.simiansuite.com` (GUI/browser), and services from `https://api.openrouteservice.org` (Python/backend), `https://autocomplete.search.hereapi.com` (GUI/browser),  and `https://lookup.search.hereapi.com` (Python/backend). Make sure these are reachable.
