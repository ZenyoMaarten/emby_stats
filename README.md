# Emby Stats

Home Assistant custom component for Emby statistics.

## Features
- Display recently added movies, series, total movies, total series, total episodes, watched/unwatched movies and series, more comming
- Customizable entity names and icons
- Automatically updates attributes from Emby server

---

## Installation Options

You can install Emby Stats via HACS or manually. Only use one method.

### Option 1: HACS Installation
1. Open Home Assistant → HACS → Integrations → “+”
2. Click Custom repositories
3. Add your GitHub repository URL: [https://github.com/ZenyoMaarten/emby_stats](https://github.com/ZenyoMaarten/emby_stats)  
   Select Integration as the type
4. Click Download
5. Go to Home Assistant → Settings → Devices & Services → Integrations → “+ Add Integration”. Search for Emby Stats and add it.
6. Restart Home Assistant after installation

### Option 2: Manual Installation
1. Download or clone the repository using:  
   `git clone https://github.com/ZenyoMaarten/emby_stats.git`
2. Copy the folder `custom_components/emby_stats/` into your Home Assistant `config/custom_components/` directory
3. The folder structure should look like this:  
   config/custom_components/emby_stats/__init__.py  
   config/custom_components/emby_stats/manifest.json  
   config/custom_components/emby_stats/strings.json
4. Restart Home Assistant after copying

---

## Configuration in Home Assistant

---

## Using the Sensor
The sensor will automatically update its state and attributes from your Emby server.

Example Lovelace cards:  

type: custom:mushroom-entity-card
icon_type: entity-picture
entity: sensor.total_movies
<img src="./screenshots/4.jpg" alt="Dashboard Example" width="400">


```yaml
type: custom:button-card
entity: sensor.last_updated_tv_shows
name: |
[[[ return entity.attributes["Item List (JSON)"][0].title; ]]]
show_name: true
show_icon: false
show_state: false
show_entity_picture: true
entity_picture: >
[[[ return ${entity.attributes["Item List (JSON)"][0].image_url}?v=${Date.now()}; ]]]
tap_action:
action: url
url_path: >
[[[ return ${entity.attributes["Item List (JSON)"][0].image_url}?v=${Date.now()}; ]]]
styles:
card:
- height: 250px
- padding: 0px
- display: flex
- flex-direction: column
- justify-content: space-between
img_cell:
- height: 200px
- width: 100%
- background-color: white
entity_picture:
- object-fit: cover
- height: 105%
- width: 105%
name:
- height: 50px
- white-space: normal
- text-align: center
- font-size: 12px
```

<img src="./screenshots/1.jpg" alt="Dashboard Example" width="400">
<img src="./screenshots/2.jpg" alt="Dashboard Example" width="400">
<img src="./screenshots/3.jpg" alt="Dashboard Example" width="400">
---

## Screenshots




---

## Notes
- Only use one installation method: HACS or manual  
- Always restart Home Assistant after installation  
- Make sure to add the integration to `configuration.yaml` for it to work  
- For issues or suggestions, open an issue on GitHub

---

## License
MIT
