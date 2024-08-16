# EV Truck route "planner"
For local usage create an free https://openrouteservice.org/ account [here](https://openrouteservice.org/dev/#/signup) and get your API key (token).

Copy the `local_application_data.json.sample` to `local_application_data.json` and store your API key (token) in `local_application_data.json`.

Make sure that simian-gui is installed (see `requirements.txt`).

To start the application run `route_planner.py`.

Note that the app uses truck images from `https://downloads.simiansuite.com` so Python should have access to that server.
